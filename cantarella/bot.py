import os
import time
import json
import asyncio
import shutil
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CREDENTIALS ---
API_ID = 
API_HASH = ""
BOT_TOKEN = ""

app = Client("gc_rclone_pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- SYSTEM CONFIGURATION ---
MAX_CONCURRENT_TASKS = 12
DAILY_LIMIT_BYTES = 30 * 1024 * 1024 * 1024  # 30 GB
CONFIG_DIR = "user_configs"
DATA_FILE = "users_data.json"
TEMP_DIR = "downloads"

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
active_tasks = {}
waiting_config = []

# --- DATABASE MANAGEMENT ---
def get_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def update_user_setting(user_id, key, value):
    data = get_data()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in data: 
        data[uid] = {"date": today, "used": 0, "auto_delete": False, "remote": ""}
        
    data[uid][key] = value
    save_data(data)

def get_user_setting(user_id, key, default=False):
    data = get_data().get(str(user_id), {})
    return data.get(key, default)

def get_user_remote(user_id, conf_path):
    saved_remote = get_user_setting(user_id, "remote", "")
    if saved_remote: return saved_remote
    
    with open(conf_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                return line.strip("[]")
    return "gdrive"

def check_and_update_limit(user_id, file_size=0):
    data = get_data()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if uid not in data:
        data[uid] = {"date": today, "used": 0, "auto_delete": False, "remote": ""}
        
    if data[uid].get("date") != today:
        data[uid]["date"] = today
        data[uid]["used"] = 0
        
    if data[uid]["used"] + file_size > DAILY_LIMIT_BYTES:
        return False 
        
    data[uid]["used"] += file_size
    save_data(data)
    return True

# --- UI & FORMATTING HELPERS ---
def human_bytes(size):
    if not size: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024

def get_dashboard_markup(user_id):
    auto_del = get_user_setting(user_id, "auto_delete", False)
    del_text = "🟢 Auto-Delete: ON" if auto_del else "🔴 Auto-Delete: OFF"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Set Config", callback_data="menu_config"),
         InlineKeyboardButton("☁️ Set Remote", callback_data="menu_remote")],
        [InlineKeyboardButton(del_text, callback_data="toggle_delete")],
        [InlineKeyboardButton("📊 Global Tasks Monitor", callback_data="menu_tasks")]
    ])
    return markup

def get_stats_text(user_id, first_name):
    data = get_data()
    uid = str(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    used = data[uid].get("used", 0) if (uid in data and data[uid].get("date") == today) else 0
    remaining = DAILY_LIMIT_BYTES - used
    
    return (
        f"👋 **Welcome to Pro Rclone Uploader, {first_name}!**\n"
        f"Upload files or direct links to your Cloud Drive seamlessly.\n\n"
        f"👤 **Account Dashboard:**\n"
        f"├ 📦 **Daily Quota:** `30.00 GB`\n"
        f"├ 🟢 **Available:** `{human_bytes(remaining)}`\n"
        f"└ 🔴 **Used:** `{human_bytes(used)}`\n\n"
        f"💡 _Select an option below to configure your workspace._"
    )

async def update_status_msg(msg, task_id, current, total, start_time, mode="📥 Downloading"):
    now = time.time()
    diff = now - start_time
    if diff < 1: return 
    
    percentage = (current * 100 / total) if total else 0
    speed = current / diff
    eta = round((total - current) / speed) if speed > 0 else 0
    
    if task_id in active_tasks:
        active_tasks[task_id].update({"status": f"{mode} {round(percentage)}%", "speed": human_bytes(speed)})

    completed = int(percentage // 10)
    bar = f"[{'█' * completed}{'░' * (10 - completed)}]"
    
    text = (
        f"🔄 **System Processing...**\n\n"
        f"**Status:** {mode}\n"
        f"{bar} **{round(percentage, 2)}%**\n\n"
        f"⚡ **Speed:** `{human_bytes(speed)}/s`\n"
        f"⏱ **ETA:** `{eta} sec`\n"
        f"💾 **Size:** `{human_bytes(current)} / {human_bytes(total)}`"
    )
    try: 
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Task", callback_data=f"cancel_{task_id}")]]))
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except: 
        pass

# --- BACKGROUND TASKS ---
async def schedule_delete(user_id, conf_path, remote_file_path):
    await asyncio.sleep(86400) # 24 Hours
    delete_cmd = ["rclone", "--config", conf_path, "deletefile", remote_file_path, "--drive-use-trash=false"]
    process = await asyncio.create_subprocess_exec(*delete_cmd)
    await process.wait()

# --- COMMANDS & CALLBACKS ---
@app.on_message(filters.command(["start", "help", "me", "stats"]))
async def start_cmd(c, m):
    await m.reply_text(
        text=get_stats_text(m.from_user.id, m.from_user.first_name),
        reply_markup=get_dashboard_markup(m.from_user.id)
    )

@app.on_message(filters.command(["setconfig", "rc"]))
async def set_config_cmd(c, m):
    waiting_config.append(m.from_user.id)
    await m.reply_text("⚙️ **Configuration Mode:**\nPlease send your `rclone.conf` file as a document.")

@app.on_message(filters.command(["setremote", "sr"]))
async def set_remote_cmd(c, m):
    if len(m.command) < 2:
        return await m.reply_text("❌ **Invalid Syntax.**\nUsage: `/sr <drive_name>`\nExample: `/sr gdrive`")
    remote_name = m.command[1]
    update_user_setting(m.from_user.id, "remote", remote_name)
    await m.reply_text(f"✅ **Success!** Default target drive updated to `{remote_name}`.")

@app.on_message(filters.command(["autodelete", "ad"]))
async def toggle_delete_cmd(c, m):
    current = get_user_setting(m.from_user.id, "auto_delete")
    new_val = not current
    update_user_setting(m.from_user.id, "auto_delete", new_val)
    status = "✅ ENABLED (24h deletion)" if new_val else "❌ DISABLED (Files kept permanently)"
    await m.reply_text(f"🛠 **Auto-Delete Status:** {status}")

@app.on_message(filters.command(["tasks", "ts"]))
async def show_all_tasks(c, m):
    if not active_tasks: return await m.reply_text("💤 **System Idle.** No active tasks in queue.")
    report = "📊 **Global Processing Monitor**\n\n"
    for tid, info in active_tasks.items():
        report += f"👤 **{info['user']}**: {info['status']} | ⚡ {info['speed']}/s\n"
    await m.reply_text(report)

@app.on_callback_query()
async def callback_handler(c, cb):
    user_id = cb.from_user.id
    data = cb.data
    
    if data.startswith("cancel_"):
        tid = data.split("_")[1]
        if tid in active_tasks:
            if active_tasks[tid]["process"]: 
                try: active_tasks[tid]["process"].terminate()
                except: pass
            active_tasks.pop(tid)
            try: await cb.message.edit_text("❌ **Task Terminated by User.**")
            except: pass
        await cb.answer("Task Cancelled.", show_alert=True)
        
    elif data == "toggle_delete":
        current = get_user_setting(user_id, "auto_delete")
        update_user_setting(user_id, "auto_delete", not current)
        await cb.message.edit_reply_markup(reply_markup=get_dashboard_markup(user_id))
        await cb.answer("Auto-Delete preference updated.")
        
    elif data == "menu_config":
        if user_id not in waiting_config: waiting_config.append(user_id)
        await cb.answer("Please send your rclone.conf file now.", show_alert=True)
        
    elif data == "menu_remote":
        await cb.answer("To set remote, send: /sr <your_drive_name>", show_alert=True)
        
    elif data == "menu_tasks":
        if not active_tasks: 
            await cb.answer("No active tasks running.", show_alert=True)
        else:
            report = "📊 Active Tasks:\n"
            for t, i in active_tasks.items(): report += f"{i['user']}: {i['status']}\n"
            await cb.answer(report[:200], show_alert=True)

# --- CORE UPLOAD ENGINE ---
async def start_process(client, message, task_id, is_url=False, url=""):
    user_id = message.from_user.id
    conf_path = os.path.join(CONFIG_DIR, f"{user_id}.conf")
    
    if not os.path.exists(conf_path):
        return await message.reply_text("❌ **Configuration Missing.**\nPlease set up your config using `/rc` first.")

    msg = await message.reply_text("⏳ **Task Added to Queue...**")
    active_tasks[task_id] = {"user": message.from_user.first_name, "status": "Queued", "speed": "0 B", "process": None}

    async with task_semaphore:
        try:
            start_time = time.time()
            file_path = ""
            
            # --- PHASE 1: DOWNLOAD ---
            if is_url:
                file_name = url.split("/")[-1].split("?")[0] or f"file_{task_id}"
                file_path = os.path.join(TEMP_DIR, file_name)
                active_tasks[task_id]["status"] = "Downloading via Aria2..."
                cmd = ["aria2c", "-x16", "-s16", "-d", TEMP_DIR, "-o", file_name, url]
                process = await asyncio.create_subprocess_exec(*cmd)
                active_tasks[task_id]["process"] = process
                await process.wait()
                
                file_size = os.path.getsize(file_path)
                if not check_and_update_limit(user_id, file_size):
                    os.remove(file_path)
                    return await msg.edit_text("❌ **Transfer Failed:** Daily 30GB Quota Exceeded.")
            else:
                file_size = (message.document or message.video or message.audio).file_size
                if not check_and_update_limit(user_id, file_size):
                    return await msg.edit_text("❌ **Transfer Failed:** Daily 30GB Quota Exceeded.")

                last_update = [time.time()]
                async def tg_prog(current, total):
                    now = time.time()
                    if now - last_update[0] > 5:
                        last_update[0] = now
                        try: await update_status_msg(msg, task_id, current, total, start_time, "📥 Downloading")
                        except FloodWait as e: await asyncio.sleep(e.value)
                        except: pass
                            
                file_path = await message.download(file_name=TEMP_DIR+"/", progress=tg_prog)

            # --- PHASE 2: UPLOAD ---
            remote = get_user_remote(user_id, conf_path)
            active_tasks[task_id]["status"] = "Uploading to Cloud..."
            await msg.edit_text(f"📤 **Uploading to `{remote}`...**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel Task", callback_data=f"cancel_{task_id}")]]))
            dest_path = f"{remote}:BotUploads/{os.path.basename(file_path)}"
            
            up_cmd = ["rclone", "--config", conf_path, "copy", file_path, f"{remote}:BotUploads"]
            r_proc = await asyncio.create_subprocess_exec(*up_cmd)
            active_tasks[task_id]["process"] = r_proc
            await r_proc.wait()

            # --- PHASE 3: GENERATE LINK ---
            active_tasks[task_id]["status"] = "Generating Link..."
            l_cmd = ["rclone", "--config", conf_path, "link", dest_path]
            l_proc = await asyncio.create_subprocess_exec(*l_cmd, stdout=asyncio.subprocess.PIPE)
            stdout, _ = await l_proc.communicate()
            link = stdout.decode().strip() or "N/A (Remote does not support public links)"

            del_mode = get_user_setting(user_id, "auto_delete")
            del_badge = "⏱️ 24h Auto-Delete: ON" if del_mode else "💾 Permanent Storage"

            final_text = (
                f"✅ **Transfer Complete!**\n\n"
                f"📄 **File:** `{os.path.basename(file_path)}`\n"
                f"☁️ **Destination:** `{remote}`\n"
                f"🛡️ **Status:** `{del_badge}`\n\n"
                f"🔗 **Public Link:**\n{link}"
            )
            
            try:
                await client.send_message(user_id, final_text)
                await msg.edit_text(f"✅ **Task Completed!**\nCheck your PM for the direct link.")
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await msg.edit_text(final_text)
            except:
                await msg.edit_text(final_text)

            # --- PHASE 4: AUTO-DELETE TIMER ---
            if del_mode:
                asyncio.create_task(schedule_delete(user_id, conf_path, dest_path))

        except FloodWait as e:
            await asyncio.sleep(e.value)
            try: await msg.edit_text("❌ **Error:** Telegram FloodWait limit hit. Please retry.")
            except: pass
        except Exception as e:
            try: await msg.edit_text(f"❌ **System Error:** `{str(e)[:200]}`")
            except FloodWait as fw: await asyncio.sleep(fw.value)
            except: pass
        finally:
            active_tasks.pop(task_id, None)
            if file_path and os.path.exists(file_path): os.remove(file_path)

# --- INCOMING MESSAGE HANDLERS ---
@app.on_message(filters.document | filters.video | filters.audio | filters.regex(r"https?://[^\s]+"))
async def handle_media(c, m):
    if m.from_user.id in waiting_config and m.document:
        if m.document.file_name.endswith(".conf"):
            await m.download(file_name=os.path.join(CONFIG_DIR, f"{m.from_user.id}.conf"))
            waiting_config.remove(m.from_user.id)
            return await m.reply_text("✅ **Configuration Saved Successfully.**\nIf you have multiple drives, use `/sr <drive_name>` to set your target.")
    
    is_url = True if m.text and "http" in m.text else False
    asyncio.create_task(start_process(c, m, str(m.id), is_url, m.text if is_url else ""))

if __name__ == "__main__":
    print("System Online: Pro Rclone Bot Initialized.")
    app.run()

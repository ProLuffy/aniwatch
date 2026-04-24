#@cantarellabots
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup
from cantarella.button import Button as InlineKeyboardButton
import asyncio
import random
import re

from cantarella.core.database import db
from cantarella.core.images import get_random_image
from cantarella.scraper.search import search_anime as search_aniwatch
from cantarella.scraper.wsearch import search_animeworld
from cantarella.scraper.cantarellatv import cantarellatvDownloader
from cantarella.core.state import current_urls, user_search_results
from cantarella.telegram.download import _handle_download
from config import OWNER_ID, TARGET_CHAT_ID, RESPONSE_IMAGES

def small_caps(text):
    data = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join([data.get(c.lower(), c) for c in text])

@Client.on_message(filters.private & filters.text & ~filters.regex(r"^/"))
async def handle_url_or_search(client: Client, message):
    url = message.text.strip()

    is_admin = await db.is_admin(message.from_user.id)
    if message.from_user.id != OWNER_ID and not is_admin:
        return await message.reply(f"<blockquote>❌ <b>{small_caps('ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs ᴄᴀɴ sᴇᴀʀᴄʜ ᴏʀ ᴅᴏᴡɴʟᴏᴀᴅ ᴀɴɪᴍᴇ.')}</b></blockquote>", parse_mode=ParseMode.HTML)

    is_url = any(domain in url.lower() for domain in ["hianime", "cantarella", "aniwatchtv.to", "animewatchtv.to", "watchanimeworld.net"])

    # --- 1. INLINE SEARCH LOGIC ---
    if not is_url:
        query = url[:50]
        try:
            random_pic = random.choice(RESPONSE_IMAGES)
        except:
            random_pic = get_random_image()

        caption = f"<blockquote>🔍 **{small_caps('sᴇᴀʀᴄʜ ǫᴜᴇʀʏ')}:** `{query}`\n\n{small_caps('ᴄʜᴏᴏsᴇ ᴀ ᴘʟᴀᴛғᴏʀᴍ ᴛᴏ sᴇᴀʀᴄʜ ғʀᴏᴍ')}:</blockquote>"
        
        buttons = [
            [
                InlineKeyboardButton(small_caps("ᴀɴɪᴡᴀᴛᴄʜ"), callback_data=f"src_ani:{query}"),
                InlineKeyboardButton(small_caps("ᴀɴɪᴍᴇ ᴡᴏʀʟᴅ"), callback_data=f"src_aw:{query}")
            ]
        ]
        
        return await client.send_photo(
            message.chat.id,
            photo=random_pic,
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )

    # --- 2. URL DOWNLOAD LOGIC ---
    is_episode = "ep=" in url or "episode-" in url

    if is_episode:
        from cantarella.telegram.pages import post_to_main_channel
        status_msg = await client.send_photo(message.chat.id, photo=get_random_image(), caption=f"<blockquote>🔄 <b>{small_caps('ᴘʀᴇᴘᴀʀɪɴɢ ᴅᴏᴡɴʟᴏᴀᴅ...')}</b></blockquote>", parse_mode=ParseMode.HTML)
        target_chat = int(TARGET_CHAT_ID) if TARGET_CHAT_ID else message.chat.id
        uploaded_msgs = await _handle_download(client, message, url, status_msg, is_playlist=False, quality="all", chat_id=target_chat)
        
        if uploaded_msgs:
            quality_map = {}
            for msg in uploaded_msgs:
                match = re.search(r'\[(\d+p)\]', msg.caption or "")
                if match:
                    quality_map[match.group(1)] = msg.id
                else:
                    quality_map["Auto"] = msg.id
            await post_to_main_channel(client, url, uploaded_msgs, quality_map)
    else:
        entries = await asyncio.to_thread(cantarellatvDownloader().list_episodes, url)
        if not entries:
            return await client.send_photo(message.chat.id, photo=get_random_image(), caption=f"<blockquote>❌ <b>{small_caps('ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴇᴘɪsᴏᴅᴇs.')}</b></blockquote>", parse_mode=ParseMode.HTML)

        count = len(entries)
        anime_title = entries[0].get('title', 'Unknown') if entries else 'Unknown'
        
        text = f"<blockquote>📺 <b>{small_caps('ᴀɴɪᴍᴇ')}:</b> {anime_title}\n📼 <b>{small_caps('ᴛᴏᴛᴀʟ ᴇᴘɪsᴏᴅᴇs')}:</b> {count}\n</blockquote>"

        await client.send_photo(message.chat.id, photo=get_random_image(), caption=text, parse_mode=ParseMode.HTML)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(small_caps("📥 ᴅᴏᴡɴʟᴏᴀᴅ ᴀʟʟ"), callback_data="download_all")], 
            [InlineKeyboardButton(small_caps("❌ ᴄᴀɴᴄᴇʟ"), callback_data="cancel")]
        ])
        await message.reply(f"<blockquote>{small_caps('ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴘᴛɪᴏɴ')}:</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)
        current_urls[message.from_user.id] = url

# --- INLINE BUTTON CALLBACKS ---
@Client.on_callback_query(filters.regex(r"^src_ani:(.*)"))
async def aniwatch_search_cb(client, callback_query):
    query = callback_query.matches[0].group(1)
    await callback_query.answer(small_caps("sᴇᴀʀᴄʜɪɴɢ ᴀɴɪᴡᴀᴛᴄʜ..."), show_alert=False)
    results = await asyncio.to_thread(search_aniwatch, query)
    
    if not results:
        return await callback_query.edit_message_caption(caption=f"<blockquote>❌ {small_caps('ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ ᴏɴ ᴀɴɪᴡᴀᴛᴄʜ ғᴏʀ')} `{query}`</blockquote>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(small_caps("⬅️ ʙᴀᴄᴋ"), callback_data=f"back_src:{query}")]]))
        
    buttons = []
    for res in results:
        buttons.append([InlineKeyboardButton(f"✅ {small_caps(res['title'][:50])}", url=res['url'])])
    
    buttons.append([InlineKeyboardButton(small_caps("⬅️ ʙᴀᴄᴋ"), callback_data=f"back_src:{query}")])
    await callback_query.edit_message_caption(caption=f"<blockquote>📺 **{small_caps('ᴀɴɪᴡᴀᴛᴄʜ ʀᴇsᴜʟᴛs')}:** `{query}`</blockquote>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^src_aw:(.*)"))
async def animeworld_search_cb(client, callback_query):
    query = callback_query.matches[0].group(1)
    await callback_query.answer(small_caps("sᴇᴀʀᴄʜɪɴɢ ᴀɴɪᴍᴇ ᴡᴏʀʟᴅ..."), show_alert=False)
    results = await asyncio.to_thread(search_animeworld, query)
    
    if not results:
        return await callback_query.edit_message_caption(caption=f"<blockquote>❌ {small_caps('ɴᴏ ʀᴇsᴜʟᴛs ғᴏᴜɴᴅ ᴏɴ ᴀɴɪᴍᴇ ᴡᴏʀʟᴅ ғᴏʀ')} `{query}`</blockquote>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(small_caps("⬅️ ʙᴀᴄᴋ"), callback_data=f"back_src:{query}")]]))
        
    buttons = []
    for res in results:
        buttons.append([InlineKeyboardButton(f"✅ {small_caps(res['title'][:50])}", url=res['url'])])
        
    buttons.append([InlineKeyboardButton(small_caps("⬅️ ʙᴀᴄᴋ"), callback_data=f"back_src:{query}")])
    await callback_query.edit_message_caption(caption=f"<blockquote>🌍 **{small_caps('ᴀɴɪᴍᴇ ᴡᴏʀʟᴅ ʀᴇsᴜʟᴛs')}:** `{query}`</blockquote>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

@Client.on_callback_query(filters.regex(r"^back_src:(.*)"))
async def back_to_sources(client, callback_query):
    query = callback_query.matches[0].group(1)
    buttons = [
        [
            InlineKeyboardButton(small_caps("ᴀɴɪᴡᴀᴛᴄʜ"), callback_data=f"src_ani:{query}"),
            InlineKeyboardButton(small_caps("ᴀɴɪᴍᴇ ᴡᴏʀʟᴅ"), callback_data=f"src_aw:{query}")
        ]
    ]
    await callback_query.edit_message_caption(caption=f"<blockquote>🔍 **{small_caps('sᴇᴀʀᴄʜ ǫᴜᴇʀʏ')}:** `{query}`\n\n{small_caps('ᴄʜᴏᴏsᴇ ᴀ ᴘʟᴀᴛғᴏʀᴍ')}:</blockquote>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)
    

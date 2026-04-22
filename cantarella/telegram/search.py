#
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

# 1. Main Text Handler (Direct Search & URLs)
@Client.on_message(filters.private & filters.text & ~filters.regex(r"^/"))
async def handle_url_or_search(client: Client, message):
    url = message.text.strip()

    # --- Access Control ---
    is_admin = await db.is_admin(message.from_user.id)
    if message.from_user.id != OWNER_ID and not is_admin:
        return await message.reply("<blockquote>❌ <b>ᴏɴʟʏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴀᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ ᴄᴀɴ ꜱᴇᴀʀᴄʜ ᴏʀ ᴅᴏᴡɴʟᴏᴀᴅ ᴀɴɪᴍᴇ.</b>\n\nᴄᴏɴᴛᴀᴄᴛ ᴛʜᴇ ᴏᴡɴᴇʀ ɪғ ʏᴏᴜ ᴛʜɪɴᴋ ᴛʜɪꜱ ɪꜱ ᴀ ᴍɪꜱᴛᴀᴋᴇ.</blockquote>", parse_mode=ParseMode.HTML)

    # Check if text is a domain URL
    is_url = any(domain in url.lower() for domain in ["hianime", "cantarella", "aniwatchtv.to", "watchanimeworld.net"])

    # --- INLINE SEARCH LOGIC ---
    if not is_url:
        query = url[:50]
        try:
            random_pic = random.choice(RESPONSE_IMAGES)
        except:
            random_pic = get_random_image()

        buttons = [
            [
                InlineKeyboardButton("Aniwatch", callback_data=f"src_ani:{query}"),
                InlineKeyboardButton("Anime World", callback_data=f"src_aw:{query}")
            ]
        ]
        
        await client.send_photo(
            message.chat.id,
            photo=random_pic,
            caption=f"<blockquote>🔍 **Search Query:** `{query}`\n\nChoose a platform to search from:</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
        return

    # --- URL DOWNLOAD LOGIC ---
    is_episode = "ep=" in url or "episode-" in url

    if is_episode:
        from cantarella.telegram.pages import post_to_main_channel
        status_msg = await client.send_photo(
            message.chat.id,
            photo=get_random_image(),
            caption="<blockquote>🔄 <b>ᴘʀᴇᴘᴀʀɪɴɢ ᴅᴏᴡɴʟᴏᴀᴅ...</b></blockquote>",
            parse_mode=ParseMode.HTML
        )
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
            await client.send_photo(
                message.chat.id,
                photo=get_random_image(),
                caption="<blockquote>❌ <b>ғᴀɪʟᴇᴅ ᴛᴏ ғᴇᴛᴄʜ ᴇᴘɪꜱᴏᴅᴇꜱ.</b></blockquote>",
                parse_mode=ParseMode.HTML
            )
            return

        count = len(entries)
        anime_title = entries[0].get('title', 'Unknown') if entries else 'Unknown'

        text = f"<blockquote>📺 <b>ᴀɴɪᴍᴇ:</b> {anime_title}\n"
        text += f"📼 <b>ᴛᴏᴛᴀʟ ᴇᴘɪꜱᴏᴅᴇꜱ:</b> {count}\n\n"
        text += "<b>ᴇᴘɪꜱᴏᴅᴇꜱ:</b>\n"
        for idx, entry in enumerate(entries, 1):
            ep_title = entry.get('title', f'Episode {idx}')
            text += f" {idx}. {ep_title}\n"
        text += "</blockquote>"

        await client.send_photo(
            message.chat.id,
            photo=get_random_image(),
            caption=text,
            parse_mode=ParseMode.HTML
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 ᴅᴏᴡɴʟᴏᴀᴅ ᴀʟʟ", callback_data="download_all")],
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="cancel")]
        ])
        await message.reply("<blockquote>ᴄʜᴏᴏꜱᴇ ᴀɴ ᴏᴘᴛɪᴏɴ:</blockquote>", reply_markup=keyboard, parse_mode=ParseMode.HTML)

        current_urls[message.from_user.id] = url

# 2. Aniwatch Search Callback
@Client.on_callback_query(filters.regex(r"^src_ani:(.*)"))
async def aniwatch_search_cb(client, callback_query):
    query = callback_query.matches[0].group(1)
    await callback_query.answer("Searching Aniwatch...", show_alert=False)
    
    results = await asyncio.to_thread(search_aniwatch, query)
    
    if not results:
        return await callback_query.edit_message_caption(
            caption=f"<blockquote>❌ No results found on Aniwatch for `{query}`.</blockquote>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"back_src:{query}")]])
        )
        
    user_search_results[callback_query.from_user.id] = results
    
    buttons = []
    for res in results:
        safe_id = res['id'][:64]
        buttons.append([InlineKeyboardButton(res['title'], callback_data=f"anime_{safe_id}")]) 
        
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_src:{query}")])
    
    await callback_query.edit_message_caption(
        caption=f"<blockquote>📺 **Aniwatch Results for:** `{query}`</blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 3. Anime World Search Callback
@Client.on_callback_query(filters.regex(r"^src_aw:(.*)"))
async def animeworld_search_cb(client, callback_query):
    query = callback_query.matches[0].group(1)
    await callback_query.answer("Searching Anime World...", show_alert=False)
    
    results = await asyncio.to_thread(search_animeworld, query)
    
    if not results:
        return await callback_query.edit_message_caption(
            caption=f"<blockquote>❌ No results found on Anime World for `{query}`.</blockquote>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data=f"back_src:{query}")]])
        )
        
    buttons = []
    for res in results:
        safe_id = res['id'][:40]
        # This callback trigger will be used later when you add anime world scraper logic
        buttons.append([InlineKeyboardButton(res['title'], callback_data=f"aw_sel_{safe_id}")]) 
        
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"back_src:{query}")])
    
    await callback_query.edit_message_caption(
        caption=f"<blockquote>🌍 **Anime World Results for:** `{query}`</blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 4. Back Button Callback
@Client.on_callback_query(filters.regex(r"^back_src:(.*)"))
async def back_to_sources(client, callback_query):
    query = callback_query.matches[0].group(1)
    buttons = [
        [
            InlineKeyboardButton("Aniwatch", callback_data=f"src_ani:{query}"),
            InlineKeyboardButton("Anime World", callback_data=f"src_aw:{query}")
        ]
    ]
    await callback_query.edit_message_caption(
        caption=f"<blockquote>🔍 **Search Query:** `{query}`\n\nChoose a platform to search from:</blockquote>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    

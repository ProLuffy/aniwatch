## +++ Made By Obito [@i_killed_my_clan] +++


from pyrogram import Client, filters
from cantarella.button import Button
from config import RESPONSE_IMAGES
import random

# Import scrapers
from cantarella.scraper.search import search_anime as search_aniwatch
from cantarella.scraper.wsearch import search_animeworld

# 1. Listen to normal text (No Commands)
@Client.on_message(filters.text & ~filters.command & filters.private)
async def auto_anime_search(client, message):
    # Limit length to 50 chars so it doesn't break Telegram's 64-byte callback limit
    query = message.text[:50] 
    
    # Select random pic from config
    random_pic = random.choice(RESPONSE_IMAGES)
    
    buttons = [
        [
            Button("Aniwatch", callback_data=f"src_ani:{query}"),
            Button("Anime World", callback_data=f"src_aw:{query}")
        ]
    ]
    
    await message.reply_photo(
        photo=random_pic,
        caption=f"<blockquote>🔍 **Search Query:** `{query}`\n\nChoose a platform to search from:</blockquote>",
        reply_markup={"inline_keyboard": buttons}
    )


# 2. Handler for Aniwatch Button
@Client.on_callback_query(filters.regex(r"^src_ani:(.*)"))
async def aniwatch_search_cb(client, callback_query):
    query = callback_query.matches[0].group(1)
    await callback_query.answer("Searching Aniwatch...", show_alert=False)
    
    results = search_aniwatch(query)
    
    if not results:
        return await callback_query.edit_message_caption(
            caption=f"<blockquote>❌ No results found on Aniwatch for `{query}`.</blockquote>",
            reply_markup={"inline_keyboard": [[Button("⬅️ Back", callback_data=f"back_src:{query}")]]}
        )
        
    buttons = []
    for res in results:
        # Pushing to your existing download/anime callback logic
        buttons.append([Button(res['title'], callback_data=f"anime:{res['id']}")]) 
        
    buttons.append([Button("⬅️ Back", callback_data=f"back_src:{query}")])
    
    await callback_query.edit_message_caption(
        caption=f"<blockquote>📺 **Aniwatch Results for:** `{query}`</blockquote>",
        reply_markup={"inline_keyboard": buttons}
    )


# 3. Handler for Anime World Button
@Client.on_callback_query(filters.regex(r"^src_aw:(.*)"))
async def animeworld_search_cb(client, callback_query):
    query = callback_query.matches[0].group(1)
    await callback_query.answer("Searching Anime World...", show_alert=False)
    
    results = search_animeworld(query)
    
    if not results:
        return await callback_query.edit_message_caption(
            caption=f"<blockquote>❌ No results found on Anime World for `{query}`.</blockquote>",
            reply_markup={"inline_keyboard": [[Button("⬅️ Back", callback_data=f"back_src:{query}")]]}
        )
        
    buttons = []
    for res in results:
        # Truncating ID to prevent 64-byte limit crash
        safe_id = res['id'][:40]
        # You will need to create another handler for 'aw_sel:' to extract episodes from Anime World later
        buttons.append([Button(res['title'], callback_data=f"aw_sel:{safe_id}")]) 
        
    buttons.append([Button("⬅️ Back", callback_data=f"back_src:{query}")])
    
    await callback_query.edit_message_caption(
        caption=f"<blockquote>🌍 **Anime World Results for:** `{query}`</blockquote>",
        reply_markup={"inline_keyboard": buttons}
    )


# 4. Back Button logic
@Client.on_callback_query(filters.regex(r"^back_src:(.*)"))
async def back_to_sources(client, callback_query):
    query = callback_query.matches[0].group(1)
    buttons = [
        [
            Button("Aniwatch", callback_data=f"src_ani:{query}"),
            Button("Anime World", callback_data=f"src_aw:{query}")
        ]
    ]
    await callback_query.edit_message_caption(
        caption=f"<blockquote>🔍 **Search Query:** `{query}`\n\nChoose a platform to search from:</blockquote>",
        reply_markup={"inline_keyboard": buttons}
    )
  

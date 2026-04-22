#@cantarellabots
from pyrogram.types import InlineKeyboardButton as PyroButton

class Button(PyroButton):
    def __init__(self, text, callback_data=None, url=None, web_app=None,
                 login_url=None, user_id=None, switch_inline_query=None,
                 switch_inline_query_current_chat=None, callback_game=None,
                 requires_password=None, pay=None, copy_text=None,
                 icon_custom_emoji_id=None, style=None, **kwargs):
        
        # Style aur colors ka logic hata diya gaya hai taaki standard Pyrogram support kare.
        
        # Pyrogram InlineKeyboardButton params
        btn_kwargs = {
            "text": text,
            "callback_data": callback_data,
            "url": url,
            "web_app": web_app,
            "login_url": login_url,
            "user_id": user_id,
            "switch_inline_query": switch_inline_query,
            "switch_inline_query_current_chat": switch_inline_query_current_chat,
            "callback_game": callback_game,
            "pay": pay
        }
        
        # Filter out None values to prevent parameter errors in older Pyrogram versions
        btn_kwargs = {k: v for k, v in btn_kwargs.items() if v is not None}

        super().__init__(**btn_kwargs)

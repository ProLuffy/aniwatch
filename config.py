#@cantarellabots
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ.get("API_ID", "21352768"))
API_HASH = os.environ.get("API_HASH", "5fecf44f5dd9f46410d6d835491ae4a3")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8047158900:AAHE8Q0A6Eb2JvbCPFfTaJSY0MqsFSWw1TU")

SET_INTERVAL = int(os.environ.get("SET_INTERVAL", 6))  # in seconds, default 1 hour
TARGET_CHAT_ID = os.environ.get("TARGET_CHAT_ID", "-1003693002045")
MAIN_CHANNEL = os.environ.get("MAIN_CHANNEL", "-1003693002045") # Change as needed
LOG_CHANNEL = os.environ.get("LOG_CHANNEL", "-1003693002045")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://probito140:umaid2008@cluster0.1utfc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
MONGO_NAME = os.environ.get("MONGO_NAME", "cantarellabots")
OWNER_ID = int(os.environ.get("OWNER_ID", "6497757690"))
ADMIN_URL = os.environ.get("ADMIN_URL", "ProObito")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@Obitoencbot")
FSUB_PIC = os.environ.get("FSUB_PIC", "https://files.catbox.moe/bli70r.jpg")
FSUB_LINK_EXPIRY = int(os.environ.get("FSUB_LINK_EXPIRY", 600))
START_PIC =os.environ.get("START_PIC", "https://files.catbox.moe/4b8jvw.jpg")

# ─── Filename & Caption Formats ───
FORMAT = os.environ.get("FORMAT", "[S{season} E{episode}] {title} [{quality}] [{audio}]")
CAPTION = os.environ.get("CAPTION", "[ @Novaflix {FORMAT}]")

# ─── Progress Bar Settings ───
PROGRESS_BAR = os.environ.get("PROGRESS_BAR", """
<blockquote> {bar} </blockquote>
<blockquote>📁 <b>{title}</b>
⚡ Speed: {speed}
📦 {current} / {total}</blockquote>
""")

# ─── Response Images ───
# Rotating anime images sent with every bot reply. Add as many as you like.
RESPONSE_IMAGES = [
    "https://files.catbox.moe/5oonsm.jpg",
    "https://files.catbox.moe/9ufgme.jpg",
    "https://files.catbox.moe/4b8jvw.jpg",
    "https://files.catbox.moe/bli70r.jpg",
    "https://files.catbox.moe/uce0lw.jpg",
    "https://files.catbox.moe/is7q4q.jpg"
]

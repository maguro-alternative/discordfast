import os
from dotenv import load_dotenv
load_dotenv()

class EnvConf:
    ADMIN_ID = os.getenv("ADMIN_ID")
    CHATGPT = os.getenv("CHATGPT")
    DEBUG_MODE = bool(os.environ.get('DEBUG_MODE',default=False))
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_BASE_URL = "https://discord.com/api"
    DISCORD_CALLBACK_URL = os.getenv("DISCORD_CALLBACK_URL")
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_SCOPE = os.getenv("DISCORD_SCOPE")
    DISCORD_REDIRECT_URL = f"https://discord.com/api/oauth2/authorize?response_type=code&client_id={os.getenv('DISCORD_CLIENT_ID')}&scope={os.getenv('DISCORD_SCOPE')}&redirect_uri={os.getenv('DISCORD_CALLBACK_URL')}&prompt=consent"
    ENCRYPTED_KEY = os.getenv("ENCRYPTED_KEY")
    GAME_NAME = os.getenv("GAME_NAME")
    LINE_CALLBACK_URL = os.getenv("LINE_CALLBACK_URL")
    LINE_BASE_URL = "https://api.line.me"
    LINE_BOT_URL = 'https://api.line.me/v2/bot'
    LINE_OAUTH_BASE_URL = "https://api.line.me/oauth2/v2.1"
    PGDATABASE = os.getenv("PGDATABASE")
    PGHOST = os.getenv("PGHOST")
    PGPASSWORD = os.getenv("PGPASSWORD")
    PGPORT = os.getenv("PGPORT")
    PGUSER = os.getenv("PGUSER")
    PORT = os.getenv("PORT")
    PORTS = os.getenv("PORTS")
    REACT_URL = os.getenv("REACT_URL")
    MIDDLE_KEY = os.getenv("MIDDLE_KEY")
    VOICEVOX_KEY = os.getenv("VOICEVOX_KEY")
    USER_LIMIT = os.getenv("USER_LIMIT")
    WEBHOOK = os.getenv("WEBHOOK")
    YOUTUBE_ACCESS_TOKEN = os.getenv("YOUTUBE_ACCESS_TOKEN")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
    YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN")
    YOUTUBE_PROJECT_ID = os.getenv("YOUTUBE_PROJECT_ID")
    YOUTUBE_TOKEN_EXPIRY = os.getenv("YOUTUBE_TOKEN_EXPIRY")
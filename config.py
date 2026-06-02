import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if it exists
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_OWNER_ID_RAW = os.getenv('TELEGRAM_OWNER_ID')

# Validate Telegram configuration
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("CRITICAL: TELEGRAM_BOT_TOKEN environment variable is missing!")

if not TELEGRAM_OWNER_ID_RAW:
    raise ValueError("CRITICAL: TELEGRAM_OWNER_ID environment variable is missing!")

try:
    TELEGRAM_OWNER_ID = int(TELEGRAM_OWNER_ID_RAW)
except ValueError:
    raise ValueError(f"CRITICAL: TELEGRAM_OWNER_ID must be a valid integer, got '{TELEGRAM_OWNER_ID_RAW}'")

# Notion Configuration
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

# Validate Notion configuration
if not NOTION_TOKEN:
    raise ValueError("CRITICAL: NOTION_TOKEN environment variable is missing!")
if not NOTION_DATABASE_ID:
    raise ValueError("CRITICAL: NOTION_DATABASE_ID environment variable is missing!")

# Gemini API Configuration (Optional)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Google OAuth Paths
CREDENTIALS_FILE = str(BASE_DIR / 'credentials.json')
TOKEN_FILE = str(BASE_DIR / 'token.json')

# Storage sandbox for downloads
DOWNLOADS_DIR = BASE_DIR / 'downloads'
DOWNLOADS_DIR.mkdir(exist_ok=True)

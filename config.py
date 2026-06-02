import os
import sys
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

# Validate Telegram configuration — these are mandatory
if not TELEGRAM_BOT_TOKEN:
    print("CRITICAL: TELEGRAM_BOT_TOKEN environment variable is missing!")
    sys.exit(1)

if not TELEGRAM_OWNER_ID_RAW:
    print("CRITICAL: TELEGRAM_OWNER_ID environment variable is missing!")
    sys.exit(1)

try:
    TELEGRAM_OWNER_ID = int(TELEGRAM_OWNER_ID_RAW)
except ValueError:
    print(f"CRITICAL: TELEGRAM_OWNER_ID must be a valid integer (your Telegram user ID), got '{TELEGRAM_OWNER_ID_RAW}'")
    sys.exit(1)

# Notion Configuration — optional, bot works without these (Notion commands disabled)
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

if not NOTION_TOKEN:
    print("WARNING: NOTION_TOKEN not set. Notion integration will be disabled.")
if not NOTION_DATABASE_ID:
    print("WARNING: NOTION_DATABASE_ID not set. Notion integration will be disabled.")

NOTION_ENABLED = bool(NOTION_TOKEN and NOTION_DATABASE_ID)

# Gemini API Configuration (Optional)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Google OAuth Paths
CREDENTIALS_FILE = str(BASE_DIR / 'credentials.json')
TOKEN_FILE = str(BASE_DIR / 'token.json')

# Google Token from env var (for Railway deployment)
GOOGLE_TOKEN_JSON = os.getenv('GOOGLE_TOKEN_JSON')

# Storage sandbox for downloads
DOWNLOADS_DIR = BASE_DIR / 'downloads'
DOWNLOADS_DIR.mkdir(exist_ok=True)

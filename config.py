import os
from dotenv import load_dotenv

load_dotenv()

# Bot token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin Telegram user IDs (comma-separated in .env)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Group ID for new orders
ORDERS_GROUP_ID = os.getenv("ORDERS_GROUP_ID", "").strip()

# Anti-spam: delay between messages when broadcasting (seconds)
BROADCAST_DELAY = 1.0

# Telegram API limit: max messages per second
TELEGRAM_RATE_LIMIT = 30

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "db.json")

# Bus photo file_id cache (will be updated after first send)
BUS_PHOTO_FILE_ID = None

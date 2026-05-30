import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8610959873"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

BRAND = "WebLab"
REPEAT_DISCOUNT = 10
MAX_ATTACHMENTS = 10

# Маркетплейс
MAX_LISTING_PHOTOS = 5
LISTING_TITLE_MAX = 80
LISTING_DESC_MAX = 1000

# Крипто-оплаты через CryptoBot (@CryptoBot)
# Получить токен: в @CryptoBot → Crypto Pay → Create App → API Token
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")
# Сеть: основная или testnet
CRYPTOBOT_TESTNET = os.getenv("CRYPTOBOT_TESTNET", "0") == "1"

# Часовой пояс для расписания воспитателей (UTC+7 для Томска)
TZ_OFFSET_HOURS = int(os.getenv("TZ_OFFSET_HOURS", "7"))

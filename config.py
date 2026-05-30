# Настройки бота
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8610959873"))
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Название бренда — отображается в приветствии и заголовках
BRAND = "WebLab"

# Скидка постоянным клиентам, %
REPEAT_DISCOUNT = 10

# Максимум вложений к одной заявке
MAX_ATTACHMENTS = 10

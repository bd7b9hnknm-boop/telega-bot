# Конфигурация: токен, ID администратора, путь к БД
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8610959873"))

# Файл базы данных (Railway: монтируется в /data при подключении Volume)
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Контакт для прямой связи (для кнопки в карточке заказа)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")  # без @, например "matvey"

# Размер скидки за повторное обращение, %
REPEAT_DISCOUNT = 10

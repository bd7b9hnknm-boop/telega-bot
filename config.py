# Конфигурация бота: токен и ID администратора
import os
from dotenv import load_dotenv

load_dotenv()

# Токен берётся из переменной окружения (Railway) или из .env
BOT_TOKEN = os.getenv("BOT_TOKEN", "8937205201:AAFidX-avLzqDFJL48iRYw7uDNKrNt4dLn0")

# ID администратора (куда будут приходить заявки)
ADMIN_ID = int(os.getenv("ADMIN_ID", "8610959873"))

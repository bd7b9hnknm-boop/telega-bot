# Двуязычные тексты RU/EN.
# Админ-панель — только русский. Пользовательский интерфейс — оба языка.
# Все длинные тексты, которые админ может переопределить из панели,
# читаются через get_text() с фолбэком на словарь ниже.
from typing import Optional

from config import BRAND, REPEAT_DISCOUNT
from database import get_setting

DEFAULT_LANG = "ru"
LANGS = ("ru", "en")

TEXTS = {
    "ru": {
        # --- Онбординг ---
        "choose_language": "🌐 <b>Выберите язык / Choose your language</b>",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",

        "choose_purpose": (
            f"<b>Добро пожаловать в {BRAND}.</b>\n\n"
            "Пожалуйста, укажите, по какому вопросу вы обращаетесь."
        ),
        "btn_purpose_ttzht": "🎓 Я студент ТТЖТ",
        "btn_purpose_other": "❓ Другое",

        "blocked": (
            "🚫 <b>Доступ ограничен.</b>\n\n"
            "Бот работает только со студентами общежития ТТЖТ.\n"
            "Если произошла ошибка — обратитесь в поддержку."
        ),

        # --- Главное меню ---
        "welcome": (
            f"<b>Добрый день, {{name}}.</b>\n\n"
            f"Это официальный бот <b>{BRAND}</b> — разработка курсовых "
            "и веб-проектов для студентов ТТЖТ.\n\n"
            "Что доступно:\n"
            "• ознакомиться с услугами и тарифами;\n"
            "• оставить заявку с вложениями;\n"
            "• отслеживать статус ваших заказов.\n\n"
            "<i>Выберите раздел в меню ниже.</i>"
        ),
        "main_menu_header": "<b>🏠 Главное меню</b>\n\n<i>Выберите раздел.</i>",

        "btn_coursework": "📄 Курсовые",
        "btn_websites":   "🌐 Сайты",
        "btn_small":      "🔧 Доп. услуги",
        "btn_order":      "📩 Оставить заявку",
        "btn_my_orders":  "📂 Мои заявки",
        "btn_terms":      "ℹ️ Условия",
        "btn_contacts":   "📞 Поддержка",
        "btn_lang":       "🌐 Язык",
        "btn_home":       "🏠 В главное меню",
        "btn_back":       "◀️ Назад",
        "btn_cancel":     "❌ Отменить",
        "btn_order_here": "📩 Заказать из этой категории",

        # --- Категории / контент ---
        "cat_coursework_title": "📄 Курсовые работы",
        "cat_websites_title":   "🌐 Веб-разработка",
        "cat_small_title":      "🔧 Дополнительные услуги",

        "terms": (
            "<b>ℹ️ Условия сотрудничества</b>\n\n"
            "<b>Оплата</b>\n"
            "▸ Предоплата 100% до начала работы\n"
            "▸ Реквизиты направляются после подтверждения заявки\n\n"
            "<b>Сроки</b>\n"
            "▸ Стандарт: 2–5 дней\n"
            "▸ Срочные заказы согласовываются отдельно\n\n"
            "<b>Гарантии</b>\n"
            "▸ Передача исходных файлов\n"
            "▸ Пояснения по работе при необходимости\n"
            "▸ Бесплатные правки в рамках ТЗ\n\n"
            "<b>Лояльность</b>\n"
            f"▸ Скидка {REPEAT_DISCOUNT}% при повторном обращении\n\n"
            "<blockquote>Итоговая стоимость согласовывается индивидуально.</blockquote>"
        ),
        "contacts": (
            "<b>📞 Поддержка</b>\n\n"
            "Связь с администратором — через бота. Просто оставьте заявку или "
            "напишите её в сообщении ниже — ваш запрос будет передан анонимно.\n\n"
            "<i>Среднее время ответа — до 2 часов в будни.</i>"
        ),

        # --- Заявка ---
        "order_blocked": (
            "⚠️ <b>У вас уже есть активная заявка.</b>\n\n"
            "Дождитесь её рассмотрения. Историю можно посмотреть в «Мои заявки»."
        ),
        "order_choose_category": "<b>📩 Новая заявка</b>\n\n<i>Выберите категорию услуги:</i>",
        "order_ask_task": (
            "<b>📝 Шаг 1 из 3 — Описание задачи</b>\n\n"
            "Опишите подробно: тема, требования, объём, особые пожелания.\n"
            "<i>Чем детальнее — тем точнее итоговая стоимость.</i>"
        ),
        "order_ask_deadline": (
            "<b>⏰ Шаг 2 из 3 — Срок выполнения</b>\n\n"
            "Укажите дату или количество дней.\n"
            "<i>Например: «к 12 июня» или «3 дня».</i>"
        ),
        "order_ask_files": (
            "<b>📎 Шаг 3 из 3 — Вложения</b>\n\n"
            "При необходимости прикрепите файлы: документы, архивы (zip/rar), "
            "изображения, готовые материалы.\n\n"
            "<i>Можно отправить несколько файлов подряд. Когда закончите — "
            "нажмите «Готово».</i>"
        ),
        "files_added": "✅ Файл прикреплён. Всего: {n}",
        "files_too_many": "⚠️ Достигнут лимит вложений ({n}).",
        "preview": (
            "<b>📋 Проверьте заявку перед отправкой</b>\n\n"
            "<b>Категория:</b> {cat}\n\n"
            "<b>Задача:</b>\n<blockquote>{task}</blockquote>\n"
            "<b>Срок:</b> {deadline}\n"
            "<b>Вложения:</b> {files}\n"
        ),
        "preview_discount": "\n🎁 <b>Скидка {p}%</b> за повторное обращение.",
        "preview_tail": "\n\n<i>Всё верно? Подтвердите отправку.</i>",
        "btn_attach_done": "✅ Готово",
        "btn_attach_skip": "⏭ Пропустить",
        "btn_send":        "✅ Отправить заявку",

        "order_sent": (
            "✅ <b>Заявка №{id} отправлена.</b>\n\n"
            "Администратор свяжется с вами в течение <b>2 часов</b>.\n"
            "<i>Статус — в разделе «Мои заявки».</i>"
        ),
        "order_cancelled": "❌ Оформление заявки отменено.",
        "no_orders": "<b>📂 Мои заявки</b>\n\n<i>У вас пока нет заявок.</i>",
        "my_orders_title": "<b>📂 Мои заявки</b>",

        # --- Статусы ---
        "user_accepted":  "🟢 <b>Заявка №{id} принята в работу.</b>\n\nРеквизиты придут отдельным сообщением.",
        "user_rejected":  "🔴 <b>Заявка №{id} отклонена.</b>\n\nСвяжитесь с поддержкой для уточнения.",
        "user_completed": "✅ <b>Заявка №{id} выполнена.</b>\n\nБлагодарим за обращение!",

        # --- Поддержка / анонимный чат ---
        "support_prompt": (
            "<b>✉️ Сообщение в поддержку</b>\n\n"
            "Напишите ваш вопрос одним сообщением — он будет передан администратору. "
            "Ответ придёт сюда же."
        ),
        "support_sent": "✅ Сообщение передано. Ожидайте ответа.",
        "support_reply_intro": "💬 <b>Ответ от поддержки:</b>",

        # Общие
        "validation_short": "⚠️ Слишком короткое сообщение. Опишите подробнее.",
        "validation_long":  "⚠️ Слишком длинно. Сократите, пожалуйста.",
        "send_text": "⚠️ Пожалуйста, отправьте текстовое сообщение.",
    },

    "en": {
        "choose_language": "🌐 <b>Choose your language / Выберите язык</b>",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",

        "choose_purpose": (
            f"<b>Welcome to {BRAND}.</b>\n\n"
            "Please specify the purpose of your request."
        ),
        "btn_purpose_ttzht": "🎓 I'm a TTZHT student",
        "btn_purpose_other": "❓ Other",

        "blocked": (
            "🚫 <b>Access restricted.</b>\n\n"
            "This bot serves only TTZHT dormitory students.\n"
            "If this is a mistake — contact support."
        ),

        "welcome": (
            f"<b>Hello, {{name}}.</b>\n\n"
            f"This is the official <b>{BRAND}</b> bot — coursework "
            "and web projects for TTZHT students.\n\n"
            "You can:\n"
            "• browse services and pricing;\n"
            "• submit a request with attachments;\n"
            "• track your orders.\n\n"
            "<i>Choose a section below.</i>"
        ),
        "main_menu_header": "<b>🏠 Main menu</b>\n\n<i>Choose a section.</i>",

        "btn_coursework": "📄 Coursework",
        "btn_websites":   "🌐 Websites",
        "btn_small":      "🔧 Extra services",
        "btn_order":      "📩 New request",
        "btn_my_orders":  "📂 My requests",
        "btn_terms":      "ℹ️ Terms",
        "btn_contacts":   "📞 Support",
        "btn_lang":       "🌐 Language",
        "btn_home":       "🏠 Main menu",
        "btn_back":       "◀️ Back",
        "btn_cancel":     "❌ Cancel",
        "btn_order_here": "📩 Order from this category",

        "cat_coursework_title": "📄 Coursework",
        "cat_websites_title":   "🌐 Web development",
        "cat_small_title":      "🔧 Extra services",

        "terms": (
            "<b>ℹ️ Terms of cooperation</b>\n\n"
            "<b>Payment</b>\n▸ 100% prepayment before work starts\n"
            "▸ Bank details are sent after request confirmation\n\n"
            "<b>Timing</b>\n▸ Standard: 2–5 days\n▸ Rush orders — by agreement\n\n"
            "<b>Guarantees</b>\n▸ Source files delivered\n▸ Explanations on request\n"
            "▸ Free revisions within the spec\n\n"
            "<b>Loyalty</b>\n"
            f"▸ {REPEAT_DISCOUNT}% discount on repeat orders\n\n"
            "<blockquote>Final price is agreed individually.</blockquote>"
        ),
        "contacts": (
            "<b>📞 Support</b>\n\n"
            "All communication goes through the bot — your message is forwarded "
            "anonymously.\n\n<i>Average reply time: under 2 hours on weekdays.</i>"
        ),

        "order_blocked": (
            "⚠️ <b>You already have an active request.</b>\n\n"
            "Please wait until it's reviewed. See history in «My requests»."
        ),
        "order_choose_category": "<b>📩 New request</b>\n\n<i>Choose a category:</i>",
        "order_ask_task": (
            "<b>📝 Step 1 of 3 — Task description</b>\n\n"
            "Describe in detail: topic, requirements, scope, special wishes.\n"
            "<i>The more detail — the more accurate the price.</i>"
        ),
        "order_ask_deadline": (
            "<b>⏰ Step 2 of 3 — Deadline</b>\n\n"
            "Provide a date or number of days.\n"
            "<i>For example: «by June 12» or «3 days».</i>"
        ),
        "order_ask_files": (
            "<b>📎 Step 3 of 3 — Attachments</b>\n\n"
            "Optionally attach files: documents, archives (zip/rar), images.\n\n"
            "<i>Send several files in a row, then press «Done».</i>"
        ),
        "files_added": "✅ File attached. Total: {n}",
        "files_too_many": "⚠️ Attachment limit reached ({n}).",
        "preview": (
            "<b>📋 Review your request</b>\n\n"
            "<b>Category:</b> {cat}\n\n"
            "<b>Task:</b>\n<blockquote>{task}</blockquote>\n"
            "<b>Deadline:</b> {deadline}\n"
            "<b>Attachments:</b> {files}\n"
        ),
        "preview_discount": "\n🎁 <b>{p}% discount</b> for repeat order.",
        "preview_tail": "\n\n<i>All correct? Confirm to send.</i>",
        "btn_attach_done": "✅ Done",
        "btn_attach_skip": "⏭ Skip",
        "btn_send":        "✅ Send request",

        "order_sent": (
            "✅ <b>Request №{id} sent.</b>\n\n"
            "An administrator will contact you within <b>2 hours</b>.\n"
            "<i>Status — in «My requests».</i>"
        ),
        "order_cancelled": "❌ Request creation cancelled.",
        "no_orders": "<b>📂 My requests</b>\n\n<i>No requests yet.</i>",
        "my_orders_title": "<b>📂 My requests</b>",

        "user_accepted":  "🟢 <b>Request №{id} accepted.</b>\n\nPayment details will follow.",
        "user_rejected":  "🔴 <b>Request №{id} rejected.</b>\n\nContact support for details.",
        "user_completed": "✅ <b>Request №{id} completed.</b>\n\nThank you!",

        "support_prompt": (
            "<b>✉️ Message to support</b>\n\n"
            "Send your question as one message — it will be forwarded to the administrator. "
            "The reply will arrive here."
        ),
        "support_sent": "✅ Message delivered. Please wait for a reply.",
        "support_reply_intro": "💬 <b>Support reply:</b>",

        "validation_short": "⚠️ Message too short. Please be more specific.",
        "validation_long":  "⚠️ Message too long. Please shorten it.",
        "send_text": "⚠️ Please send a text message.",
    },
}


def t(key: str, lang: Optional[str] = None) -> str:
    """Безопасный геттер строки с фолбэком RU."""
    lang = lang if lang in LANGS else DEFAULT_LANG
    return TEXTS[lang].get(key) or TEXTS[DEFAULT_LANG].get(key, key)


async def get_text(key: str, lang: Optional[str] = None) -> str:
    """То же, но сначала смотрит переопределение в БД (settings).
    Ключ в БД: text:<lang>:<key>. Если нет — берём из словаря."""
    lang = lang if lang in LANGS else DEFAULT_LANG
    custom = await get_setting(f"text:{lang}:{key}")
    if custom is not None:
        return custom
    return t(key, lang)

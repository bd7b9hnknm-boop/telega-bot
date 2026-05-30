# RU/EN тексты бота. Длинные тексты можно переопределять через админ-панель.
from typing import Optional

from config import BRAND, REPEAT_DISCOUNT
from database import get_setting

DEFAULT_LANG = "ru"
LANGS = ("ru", "en")

TEXTS = {
    "ru": {
        # ===== Онбординг =====
        "choose_language": "🌐 <b>Выберите язык / Choose your language</b>",
        "btn_lang_ru": "🇷🇺 Русский",
        "btn_lang_en": "🇬🇧 English",
        "choose_purpose": (
            f"<b>Добро пожаловать в {BRAND}.</b>\n\n"
            "Укажите, по какому вопросу вы обращаетесь."
        ),
        "btn_purpose_ttzht": "🎓 Я студент ТТЖТ",
        "btn_purpose_other": "❓ Другое",
        "blocked": (
            "🚫 <b>Доступ ограничен.</b>\n\n"
            "Бот работает только со студентами общежития ТТЖТ.\n"
            "Если произошла ошибка — обратитесь в поддержку."
        ),

        # ===== Главное меню =====
        "welcome": (
            f"<b>Добрый день, {{name}}.</b>\n\n"
            f"Это бот <b>{BRAND}</b> для студентов общежития ТТЖТ.\n\n"
            "Доступно:\n"
            "• 📚 заказ курсовых, сайтов, доп. услуг;\n"
            "• 🛒 маркетплейс объявлений;\n"
            "• 🖨 распечатка и услуги соседей;\n"
            "• 🏠 информация по общежитию;\n"
            "• 📋 шаблоны документов.\n\n"
            "<i>Выберите раздел.</i>"
        ),
        "main_menu_header": "<b>🏠 Главное меню</b>",

        "btn_study":      "📚 Учёба и проекты",
        "btn_market":     "🛒 Маркетплейс",
        "btn_print":      "🖨 Распечатка",
        "btn_notes_srv":  "📝 Конспекты на заказ",
        "btn_dorm":       "🏠 Общежитие",
        "btn_docs":       "📋 Документы",
        "btn_terms":      "ℹ️ Условия",
        "btn_contacts":   "📞 Поддержка",
        "btn_lang":       "🌐 Язык",
        "btn_home":       "🏠 Главное меню",
        "btn_back":       "◀️ Назад",
        "btn_cancel":     "❌ Отменить",

        # ===== Раздел «Учёба» =====
        "study_header": (
            "<b>📚 Учёба и проекты</b>\n\n"
            "Заказ курсовых, сайтов и сопутствующих работ."
        ),
        "btn_coursework": "📄 Курсовые",
        "btn_websites":   "🌐 Сайты",
        "btn_small":      "🔧 Доп. услуги",
        "btn_order":      "📩 Оставить заявку",
        "btn_my_orders":  "📂 Мои заявки",
        "btn_order_here": "📩 Заказать из этой категории",

        "cat_coursework_title": "📄 Курсовые работы",
        "cat_websites_title":   "🌐 Веб-разработка",
        "cat_small_title":      "🔧 Дополнительные услуги",

        "terms": (
            "<b>ℹ️ Условия сотрудничества</b>\n\n"
            "<b>Оплата</b>\n"
            "▸ Предоплата 100% до начала работы\n"
            "▸ Способы: банковская карта, СБП, криптовалюта (USDT)\n\n"
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
            "Связь с администратором — только через бота. Сообщение передаётся "
            "анонимно, ваш номер и профиль не передаются.\n\n"
            "<i>Среднее время ответа — до 2 часов в будни.</i>"
        ),

        # ===== Заявка =====
        "order_blocked": "⚠️ <b>У вас уже есть активная заявка.</b>\n\nДождитесь рассмотрения.",
        "order_choose_category": "<b>📩 Новая заявка</b>\n\n<i>Выберите категорию:</i>",
        "order_ask_task": (
            "<b>📝 Шаг 1 из 3 — Описание задачи</b>\n\n"
            "Опишите подробно: тема, требования, объём.\n"
            "<i>Чем детальнее — тем точнее итоговая стоимость.</i>"
        ),
        "order_ask_deadline": (
            "<b>⏰ Шаг 2 из 3 — Срок выполнения</b>\n\n"
            "Укажите дату или количество дней."
        ),
        "order_ask_files": (
            "<b>📎 Шаг 3 из 3 — Вложения</b>\n\n"
            "Можно прикрепить документы, архивы (zip/rar), изображения.\n"
            "<i>Когда закончите — нажмите «Готово».</i>"
        ),
        "files_added": "✅ Файл прикреплён. Всего: {n}",
        "files_too_many": "⚠️ Достигнут лимит вложений ({n}).",
        "preview": (
            "<b>📋 Проверьте заявку</b>\n\n"
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
            "Администратор свяжется с вами в течение <b>2 часов</b> "
            "для подтверждения и оплаты.\n\n"
            "<i>Статус — в разделе «Мои заявки».</i>"
        ),
        "order_cancelled": "❌ Оформление заявки отменено.",
        "no_orders": "<b>📂 Мои заявки</b>\n\n<i>Заявок пока нет.</i>",
        "my_orders_title": "<b>📂 Мои заявки</b>",

        "user_accepted":  "🟢 <b>Заявка №{id} принята.</b>\n\nДля начала работы внесите предоплату. Способ оплаты — в меню «Мои заявки».",
        "user_rejected":  "🔴 <b>Заявка №{id} отклонена.</b>\n\nПодробности можно уточнить в поддержке.",
        "user_completed": "✅ <b>Заявка №{id} выполнена.</b>\n\nБлагодарим за обращение!",

        # ===== Поддержка =====
        "support_prompt": (
            "<b>✉️ Сообщение в поддержку</b>\n\n"
            "Напишите вопрос одним сообщением — он будет анонимно передан администратору. "
            "Ответ придёт сюда."
        ),
        "support_sent": "✅ Сообщение передано. Ожидайте ответа.",
        "support_reply_intro": "💬 <b>Ответ от поддержки:</b>",

        # ===== Оплаты =====
        "pay_choose": (
            "<b>💳 Способ оплаты по заявке №{id}</b>\n\n"
            "Сумма: <b>{amount}</b>\n\n"
            "<i>Выберите удобный способ.</i>"
        ),
        "pay_card": (
            "<b>💳 Оплата картой / СБП</b>\n\n"
            "Реквизиты:\n<blockquote>{req}</blockquote>\n"
            "<b>Сумма:</b> {amount}\n\n"
            "<i>После перевода нажмите кнопку «Я оплатил» — администратор сверит и подтвердит.</i>"
        ),
        "pay_crypto_intro": (
            "<b>🪙 Оплата криптовалютой (USDT)</b>\n\n"
            "Будет создан счёт через @CryptoBot. Оплата подтверждается автоматически."
        ),
        "pay_crypto_invoice": (
            "🪙 <b>Счёт создан.</b>\n\n"
            "Сумма: <b>{amount} USDT</b>\n\n"
            "Нажмите кнопку для оплаты в @CryptoBot. После оплаты статус "
            "обновится автоматически в течение минуты."
        ),
        "pay_card_claimed": "✅ Платёж отмечен как отправленный. Ожидайте сверки администратором.",
        "btn_pay_card":   "💳 Карта / СБП",
        "btn_pay_crypto": "🪙 Крипто (USDT)",
        "btn_pay_done":   "✅ Я оплатил",
        "btn_pay_open":   "🔗 Открыть счёт",
        "pay_no_methods": "⚠️ Сейчас способы оплаты не настроены. Свяжитесь с поддержкой.",

        # ===== Маркетплейс =====
        "market_header": (
            "<b>🛒 Маркетплейс</b>\n\n"
            "Объявления студентов общежития. <i>Сделки заключаются между "
            "покупателем и продавцом напрямую, без участия администрации. "
            "За товар и оплату отвечают стороны.</i>"
        ),
        "btn_market_browse": "📂 Смотреть объявления",
        "btn_market_create": "➕ Добавить объявление",
        "btn_market_mine":   "📋 Мои объявления",
        "btn_market_rules":  "📜 Правила",

        "market_rules": (
            "<b>📜 Правила маркетплейса</b>\n\n"
            "▸ Все объявления проходят премодерацию\n"
            "▸ Связь покупатель ↔ продавец — анонимно через бота\n"
            "▸ Контакты передаются по обоюдному согласию\n"
            "▸ Оплата — при встрече или по договорённости сторон\n"
            "▸ Запрещены: оружие, наркотики, краденое, оскорбления\n"
            "▸ Категория «18+» доступна после подтверждения возраста"
        ),

        "btn_market_cat_books":   "📚 Учебники / конспекты",
        "btn_market_cat_clothes": "👕 Одежда / обувь",
        "btn_market_cat_tech":    "💻 Техника",
        "btn_market_cat_other":   "📦 Прочее",
        "btn_market_cat_18":      "🔞 18+ (вейпы, жижи)",
        "btn_market_cat_vpn":     "🛡 VPN (в разработке)",

        "vpn_wip": "🛠 <b>Раздел в разработке.</b>\n\nСкоро здесь появятся объявления.",

        "age_gate": (
            "🔞 <b>Раздел только для лиц старше 18 лет</b>\n\n"
            "Содержит объявления о никотинсодержащих жидкостях и устройствах "
            "(вейпы, жижи). Покупка и продажа таких товаров — на ваш страх и риск; "
            "ответственность за оборот лежит на сторонах сделки.\n\n"
            "Подтвердите, что вам исполнилось 18 лет."
        ),
        "btn_age_yes": "✅ Мне есть 18",
        "btn_age_no":  "❌ Нет",
        "age_denied":  "🚫 Раздел недоступен.",

        "market_empty": "📭 <i>В этой категории пока нет объявлений.</i>",

        "create_choose_category": "<b>➕ Новое объявление</b>\n\nВыберите категорию:",
        "create_ask_title": "<b>📝 Шаг 1 — Заголовок</b>\n\n<i>Кратко: что продаёте.</i>",
        "create_ask_desc":  "<b>📄 Шаг 2 — Описание</b>\n\n<i>Состояние, особенности, причина продажи.</i>",
        "create_ask_price": "<b>💰 Шаг 3 — Цена</b>\n\n<i>Например: 500 ₽ или «договорная».</i>",
        "create_ask_photos": (
            "<b>🖼 Шаг 4 — Фото</b>\n\n"
            "Прикрепите до {n} фото. Когда закончите — «Готово».\n"
            "<i>Можно пропустить — но с фото объявления заметнее.</i>"
        ),
        "create_preview": (
            "<b>📋 Проверьте объявление</b>\n\n"
            "<b>Категория:</b> {cat}\n"
            "<b>Заголовок:</b> {title}\n"
            "<b>Цена:</b> {price}\n"
            "<b>Фото:</b> {photos}\n\n"
            "{desc}\n\n"
            "<i>После отправки оно пройдёт модерацию.</i>"
        ),
        "create_sent": (
            "✅ <b>Объявление №{id} отправлено на модерацию.</b>\n\n"
            "После проверки оно появится в общем списке. "
            "Уведомление придёт сюда."
        ),

        "listing_card": (
            "<b>{title}</b>\n\n"
            "💰 <b>{price}</b>\n"
            "📂 {cat}\n\n"
            "{desc}\n\n"
            "<i>Объявление №{id}</i>"
        ),
        "btn_listing_buy": "✉️ Написать продавцу",
        "btn_listing_next": "➡️ Следующее",
        "btn_listing_prev": "⬅️ Предыдущее",
        "btn_listing_close_my": "🗑 Снять",
        "btn_listing_sold": "✅ Отметить продано",

        "chat_started": (
            "💬 <b>Анонимный чат с продавцом по объявлению №{id}</b>\n\n"
            "Все сообщения передаются через бота. Имена и контакты скрыты.\n"
            "Для выхода — /stop."
        ),
        "chat_started_seller": (
            "💬 <b>Покупатель пишет по вашему объявлению №{id}</b>\n\n"
            "Сообщения анонимны. Для выхода из чата — /stop."
        ),
        "chat_msg_intro": "💬 <i>Новое сообщение по объявлению №{id}:</i>",
        "chat_ended": "🛑 Чат завершён.",
        "chat_partner_left": "🛑 Собеседник вышел из чата.",
        "chat_delivered": "✓",
        "chat_failed": "⚠️ Не доставлено",

        # ===== Распечатка / конспекты =====
        "print_header": (
            "<b>🖨 Распечатка</b>\n\n"
            "В общежитии печатают в нескольких комнатах. "
            "Выберите того, кто сейчас на связи."
        ),
        "notes_header": (
            "<b>📝 Конспекты на заказ</b>\n\n"
            "Список ребят, которые пишут конспекты под заказ."
        ),
        "provider_empty": "<i>Список пока пуст. Загляните позже.</i>",
        "provider_card": (
            "<b>{name}</b>\n"
            "{room}{contact}{price}{note}"
        ),

        # ===== Общага =====
        "dorm_header": "<b>🏠 Общежитие ТТЖТ</b>\n\n<i>Выберите раздел.</i>",
        "btn_dorm_pay":   "💰 Оплата проживания",
        "btn_dorm_duty":  "👤 Кто сегодня дежурит",
        "btn_dorm_info":  "ℹ️ Полезная информация",

        "dorm_pay_default": (
            "<b>💰 Оплата проживания</b>\n\n"
            "Информация ещё не настроена администратором."
        ),
        "dorm_info_default": (
            "<b>ℹ️ Полезная информация</b>\n\n"
            "Информация ещё не настроена администратором."
        ),
        "btn_dorm_pay_link": "🔗 Перейти к оплате (Сбер)",

        # ===== Воспитатели =====
        "duty_header": "<b>👤 Дежурные сегодня</b>",
        "duty_main":  "🌅 Главный воспитатель (с утра до обеда):",
        "duty_floor2": "🏢 2 этаж:",
        "duty_floor3": "🏢 3 этаж:",
        "duty_none": "<i>не назначен</i>",
        "duty_skip": "<i>выходной</i>",
        "duty_not_setup": (
            "<b>👤 Дежурства</b>\n\n"
            "Список воспитателей ещё не настроен."
        ),

        # ===== Документы =====
        "docs_header": (
            "<b>📋 Шаблоны документов</b>\n\n"
            "Заявления, объяснительные и другие шаблоны. "
            "Нажмите на нужный — бот пришлёт файл."
        ),
        "docs_empty": "<i>Документов пока нет.</i>",

        # ===== Общие =====
        "validation_short": "⚠️ Слишком короткое сообщение.",
        "validation_long":  "⚠️ Слишком длинно. Сократите.",
        "send_text": "⚠️ Пожалуйста, отправьте текст.",
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
        "blocked": "🚫 <b>Access restricted.</b>\n\nThis bot serves only TTZHT students.",

        "welcome": (
            f"<b>Hello, {{name}}.</b>\n\n"
            f"This is the <b>{BRAND}</b> bot for TTZHT dormitory students.\n\n"
            "Available:\n"
            "• 📚 coursework & web projects;\n"
            "• 🛒 marketplace;\n"
            "• 🖨 printing & roommate services;\n"
            "• 🏠 dorm info;\n"
            "• 📋 document templates.\n\n"
            "<i>Choose a section.</i>"
        ),
        "main_menu_header": "<b>🏠 Main menu</b>",

        "btn_study":      "📚 Study & Projects",
        "btn_market":     "🛒 Marketplace",
        "btn_print":      "🖨 Printing",
        "btn_notes_srv":  "📝 Note-taking",
        "btn_dorm":       "🏠 Dormitory",
        "btn_docs":       "📋 Documents",
        "btn_terms":      "ℹ️ Terms",
        "btn_contacts":   "📞 Support",
        "btn_lang":       "🌐 Language",
        "btn_home":       "🏠 Main menu",
        "btn_back":       "◀️ Back",
        "btn_cancel":     "❌ Cancel",

        "study_header": "<b>📚 Study & Projects</b>",
        "btn_coursework": "📄 Coursework",
        "btn_websites":   "🌐 Websites",
        "btn_small":      "🔧 Extra services",
        "btn_order":      "📩 New request",
        "btn_my_orders":  "📂 My requests",
        "btn_order_here": "📩 Order from this category",

        "cat_coursework_title": "📄 Coursework",
        "cat_websites_title":   "🌐 Web development",
        "cat_small_title":      "🔧 Extra services",

        "terms": (
            "<b>ℹ️ Terms</b>\n\n"
            "<b>Payment</b>\n▸ 100% prepayment\n▸ Card, SBP, USDT\n\n"
            "<b>Timing</b>\n▸ 2–5 days\n\n"
            "<b>Guarantees</b>\n▸ Sources delivered\n▸ Free revisions within spec\n\n"
            f"<b>Loyalty</b>\n▸ {REPEAT_DISCOUNT}% repeat discount"
        ),
        "contacts": "<b>📞 Support</b>\n\nAll communication via the bot — anonymously.",

        "order_blocked": "⚠️ <b>You already have an active request.</b>",
        "order_choose_category": "<b>📩 New request</b>\n\nChoose category:",
        "order_ask_task": "<b>📝 Step 1/3 — Description</b>\n\nDescribe in detail.",
        "order_ask_deadline": "<b>⏰ Step 2/3 — Deadline</b>",
        "order_ask_files": "<b>📎 Step 3/3 — Attachments</b>\n\nOptional. Press Done when ready.",
        "files_added": "✅ Attached. Total: {n}",
        "files_too_many": "⚠️ Limit reached ({n}).",
        "preview": (
            "<b>📋 Review</b>\n\n"
            "<b>Category:</b> {cat}\n\n"
            "<b>Task:</b>\n<blockquote>{task}</blockquote>\n"
            "<b>Deadline:</b> {deadline}\n"
            "<b>Files:</b> {files}\n"
        ),
        "preview_discount": "\n🎁 <b>{p}% discount</b>.",
        "preview_tail": "\n\n<i>Confirm to send.</i>",
        "btn_attach_done": "✅ Done",
        "btn_attach_skip": "⏭ Skip",
        "btn_send":        "✅ Send",

        "order_sent": "✅ <b>Request №{id} sent.</b>",
        "order_cancelled": "❌ Cancelled.",
        "no_orders": "<b>📂 My requests</b>\n\n<i>No requests yet.</i>",
        "my_orders_title": "<b>📂 My requests</b>",

        "user_accepted":  "🟢 <b>Request №{id} accepted.</b>\n\nPayment details follow.",
        "user_rejected":  "🔴 <b>Request №{id} rejected.</b>",
        "user_completed": "✅ <b>Request №{id} completed.</b>",

        "support_prompt": "<b>✉️ Message support</b>\n\nSend a single message.",
        "support_sent": "✅ Delivered.",
        "support_reply_intro": "💬 <b>Support reply:</b>",

        "pay_choose": "<b>💳 Payment for request №{id}</b>\n\nAmount: <b>{amount}</b>",
        "pay_card": "<b>💳 Card / SBP</b>\n\n<blockquote>{req}</blockquote>\nAmount: {amount}",
        "pay_crypto_intro": "<b>🪙 Crypto (USDT)</b>\n\nInvoice via @CryptoBot.",
        "pay_crypto_invoice": "🪙 <b>Invoice created.</b>\n\nAmount: <b>{amount} USDT</b>",
        "pay_card_claimed": "✅ Marked as paid. Awaiting admin confirmation.",
        "btn_pay_card":   "💳 Card / SBP",
        "btn_pay_crypto": "🪙 Crypto (USDT)",
        "btn_pay_done":   "✅ I have paid",
        "btn_pay_open":   "🔗 Open invoice",
        "pay_no_methods": "⚠️ Payment is not configured yet.",

        "market_header": "<b>🛒 Marketplace</b>\n\n<i>Trade between students. Admin is not part of the deal.</i>",
        "btn_market_browse": "📂 Browse",
        "btn_market_create": "➕ New listing",
        "btn_market_mine":   "📋 My listings",
        "btn_market_rules":  "📜 Rules",
        "market_rules": "<b>📜 Marketplace rules</b>\n\n▸ All listings moderated\n▸ Anonymous chat\n▸ Payment off-bot",
        "btn_market_cat_books":   "📚 Books / notes",
        "btn_market_cat_clothes": "👕 Clothes",
        "btn_market_cat_tech":    "💻 Electronics",
        "btn_market_cat_other":   "📦 Other",
        "btn_market_cat_18":      "🔞 18+ (vape, liquids)",
        "btn_market_cat_vpn":     "🛡 VPN (WIP)",
        "vpn_wip": "🛠 <b>Section under development.</b>",
        "age_gate": "🔞 <b>18+ section</b>\n\nConfirm you are 18 or older.",
        "btn_age_yes": "✅ I'm 18+",
        "btn_age_no":  "❌ No",
        "age_denied":  "🚫 Section unavailable.",
        "market_empty": "📭 <i>No listings in this category yet.</i>",

        "create_choose_category": "<b>➕ New listing</b>\n\nChoose category:",
        "create_ask_title": "<b>📝 Step 1 — Title</b>",
        "create_ask_desc":  "<b>📄 Step 2 — Description</b>",
        "create_ask_price": "<b>💰 Step 3 — Price</b>",
        "create_ask_photos": "<b>🖼 Step 4 — Photos</b>\n\nUp to {n} photos. Press Done when ready.",
        "create_preview": (
            "<b>📋 Review listing</b>\n\n"
            "<b>Category:</b> {cat}\n<b>Title:</b> {title}\n"
            "<b>Price:</b> {price}\n<b>Photos:</b> {photos}\n\n{desc}"
        ),
        "create_sent": "✅ <b>Listing №{id} sent for moderation.</b>",

        "listing_card": "<b>{title}</b>\n\n💰 <b>{price}</b>\n📂 {cat}\n\n{desc}\n\n<i>#{id}</i>",
        "btn_listing_buy": "✉️ Message seller",
        "btn_listing_next": "➡️ Next",
        "btn_listing_prev": "⬅️ Prev",
        "btn_listing_close_my": "🗑 Remove",
        "btn_listing_sold": "✅ Mark sold",
        "chat_started": "💬 <b>Anonymous chat with seller, listing №{id}</b>\n\n/stop to leave.",
        "chat_started_seller": "💬 <b>Buyer messaging you about listing №{id}</b>\n\n/stop to leave.",
        "chat_msg_intro": "💬 <i>New message on listing №{id}:</i>",
        "chat_ended": "🛑 Chat ended.",
        "chat_partner_left": "🛑 Your partner left the chat.",
        "chat_delivered": "✓",
        "chat_failed": "⚠️ Not delivered",

        "print_header": "<b>🖨 Printing</b>\n\nProviders in the dorm:",
        "notes_header": "<b>📝 Note-taking on demand</b>",
        "provider_empty": "<i>No providers yet.</i>",
        "provider_card": "<b>{name}</b>\n{room}{contact}{price}{note}",

        "dorm_header": "<b>🏠 TTZHT dormitory</b>",
        "btn_dorm_pay":   "💰 Accommodation fee",
        "btn_dorm_duty":  "👤 Today's supervisors",
        "btn_dorm_info":  "ℹ️ Useful info",
        "dorm_pay_default": "<b>💰 Accommodation fee</b>\n\nNot configured.",
        "dorm_info_default": "<b>ℹ️ Info</b>\n\nNot configured.",
        "btn_dorm_pay_link": "🔗 Open payment (Sber)",

        "duty_header": "<b>👤 Supervisors today</b>",
        "duty_main":  "🌅 Head supervisor (morning):",
        "duty_floor2": "🏢 Floor 2:",
        "duty_floor3": "🏢 Floor 3:",
        "duty_none": "<i>not set</i>",
        "duty_skip": "<i>day off</i>",
        "duty_not_setup": "<b>👤 Duty</b>\n\nSupervisors list is not configured yet.",

        "docs_header": "<b>📋 Document templates</b>\n\nTap a title to get the file.",
        "docs_empty": "<i>No documents yet.</i>",

        "validation_short": "⚠️ Too short.",
        "validation_long":  "⚠️ Too long.",
        "send_text": "⚠️ Please send a text message.",
    },
}


def t(key: str, lang: Optional[str] = None) -> str:
    lang = lang if lang in LANGS else DEFAULT_LANG
    return TEXTS[lang].get(key) or TEXTS[DEFAULT_LANG].get(key, key)


async def get_text(key: str, lang: Optional[str] = None) -> str:
    """С учётом переопределения из БД."""
    lang = lang if lang in LANGS else DEFAULT_LANG
    custom = await get_setting(f"text:{lang}:{key}")
    if custom is not None:
        return custom
    return t(key, lang)

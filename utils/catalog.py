# Каталог услуг. Цены в рублях, перевод на EN — для удобства.
from utils.i18n import t

CATALOG = {
    "coursework": {
        "title_key": "cat_coursework_title",
        "intro": {
            "ru": "Направление «Разработка веб и мультимедийных приложений». Сопровождение от ТЗ до защиты.",
            "en": "Web & multimedia development specialty. Full support from spec to defence.",
        },
        "items": [
            {"ru": "Только пояснительная записка", "en": "Report only",
             "price": "1 000 ₽", "term_ru": "3–5 дней", "term_en": "3–5 days"},
            {"ru": "Записка + сайт", "en": "Report + website",
             "price": "2 500 ₽", "term_ru": "4–5 дней", "term_en": "4–5 days"},
            {"ru": "Записка + сайт + презентация", "en": "Report + website + slides",
             "price": "3 500 ₽", "term_ru": "5 дней", "term_en": "5 days"},
        ],
    },
    "websites": {
        "title_key": "cat_websites_title",
        "intro": {
            "ru": "Адаптивная вёрстка, чистый код, исходники передаются заказчику.",
            "en": "Responsive layout, clean code, sources delivered to the client.",
        },
        "items": [
            {"ru": "Лендинг / одностраничник", "en": "Landing page",
             "price": "1 000 – 1 500 ₽", "term_ru": "2–3 дня", "term_en": "2–3 days"},
            {"ru": "Многостраничный (HTML/CSS/JS)", "en": "Multipage (HTML/CSS/JS)",
             "price": "2 000 – 3 000 ₽", "term_ru": "3–5 дней", "term_en": "3–5 days"},
            {"ru": "Сайт с БД, авторизацией, функционалом",
             "en": "Site with DB, auth, custom features",
             "price": "3 500 – 5 000 ₽", "term_ru": "5 дней", "term_en": "5 days"},
        ],
    },
    "small": {
        "title_key": "cat_small_title",
        "intro": {
            "ru": "Точечные задачи и доработки.",
            "en": "Small tasks and improvements.",
        },
        "items": [
            {"ru": "Правки и доработка сайта", "en": "Website tweaks",
             "price": "от 300 ₽ / from 300 ₽", "term_ru": "по объёму", "term_en": "by scope"},
            {"ru": "Презентация", "en": "Presentation",
             "price": "от 500 ₽ / from 500 ₽", "term_ru": "1–2 дня", "term_en": "1–2 days"},
            {"ru": "Отчёт / объяснительная", "en": "Report / explanatory note",
             "price": "от 400 ₽ / from 400 ₽", "term_ru": "1–2 дня", "term_en": "1–2 days"},
            {"ru": "Исправление ошибок в коде", "en": "Bug fixing",
             "price": "от 300 ₽ / from 300 ₽", "term_ru": "по объёму", "term_en": "by scope"},
        ],
    },
}


def category_title(key: str, lang: str) -> str:
    return t(CATALOG[key]["title_key"], lang)


def render_category(key: str, lang: str) -> str:
    cat = CATALOG[key]
    title = category_title(key, lang)
    intro = cat["intro"].get(lang, cat["intro"]["ru"])
    lines = [f"<b>{title}</b>", "", f"<i>{intro}</i>", ""]
    for item in cat["items"]:
        name = item.get(lang, item["ru"])
        term = item.get(f"term_{lang}", item["term_ru"])
        lines.append(f"▸ <b>{name}</b>\n   💰 {item['price']}   •   ⏱ {term}")
        lines.append("")
    tail_ru = "Чтобы оставить заявку — нажмите кнопку ниже."
    tail_en = "To submit a request — press the button below."
    lines.append(f"<blockquote>{tail_en if lang == 'en' else tail_ru}</blockquote>")
    return "\n".join(lines)

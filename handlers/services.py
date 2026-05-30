# Список исполнителей по услугам: распечатка и конспекты на заказ.
# Управляется админ-панелью. Юзер видит карточки.
from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import get_user, list_providers
from utils.i18n import t, get_text
from keyboards.inline import services_back

router = Router()


SERVICE_HEADER_KEY = {
    "print": "print_header",
    "notes": "notes_header",
}


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


def _render_provider(p: dict, lang: str) -> str:
    room    = (f"\n🚪 {('Комната' if lang == 'ru' else 'Room')}: {p['room']}" if p.get("room") else "")
    contact = (f"\n📱 {('Связь' if lang == 'ru' else 'Contact')}: {p['contact']}" if p.get("contact") else "")
    price   = (f"\n💰 {p['price_info']}" if p.get("price_info") else "")
    note    = (f"\n📝 {p['note']}" if p.get("note") else "")
    return t("provider_card", lang).format(
        name=p["name"], room=room, contact=contact, price=price, note=note,
    )


@router.callback_query(F.data.startswith("srv:"))
async def show_service(call: CallbackQuery, db_user=None):
    service = call.data.split(":", 1)[1]
    if service not in SERVICE_HEADER_KEY:
        await call.answer(); return
    lang = _lang(db_user or await get_user(call.from_user.id))
    providers = await list_providers(service, only_active=True)

    header = await get_text(SERVICE_HEADER_KEY[service], lang)
    if not providers:
        text = f"{header}\n\n{t('provider_empty', lang)}"
    else:
        cards = [_render_provider(p, lang) for p in providers]
        text = header + "\n\n" + "\n\n".join(cards)
    try:
        await call.message.edit_text(text, reply_markup=services_back(lang))
    except Exception:
        await call.message.answer(text, reply_markup=services_back(lang))
    await call.answer()

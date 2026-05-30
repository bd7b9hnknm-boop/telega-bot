# Маркетплейс: каталог, просмотр объявлений, создание, мои объявления,
# анонимный чат покупатель ↔ продавец через бота.
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message, InputMediaPhoto,
)
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, MAX_LISTING_PHOTOS, LISTING_TITLE_MAX, LISTING_DESC_MAX
from database import (
    get_user, set_user_field,
    create_listing, add_listing_photo, get_listing, listing_photos,
    list_listings, my_listings, set_listing_status,
    L_ACTIVE, L_PENDING, L_SOLD, L_REMOVED, L_LABELS,
)
from utils.i18n import t, get_text
from keyboards.inline import (
    main_menu, market_root, market_categories, age_gate_kb,
    listing_nav, my_listing_actions, listing_photos_done,
    listing_create_confirm, listing_create_cancel, chat_kb,
    back_home,
)
from keyboards.admin import listing_moderate_kb
from states.order import ListingCreate, P2PChat

router = Router()


CATEGORY_LABELS = {
    "books":   {"ru": "📚 Учебники / конспекты", "en": "📚 Books / notes"},
    "clothes": {"ru": "👕 Одежда / обувь",       "en": "👕 Clothes"},
    "tech":    {"ru": "💻 Техника",               "en": "💻 Electronics"},
    "other":   {"ru": "📦 Прочее",                "en": "📦 Other"},
    "18plus":  {"ru": "🔞 18+ (вейпы, жижи)",     "en": "🔞 18+ (vape)"},
    "vpn":     {"ru": "🛡 VPN",                   "en": "🛡 VPN"},
}


def cat_label(key: str, lang: str) -> str:
    return CATEGORY_LABELS.get(key, {}).get(lang, key)


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


# ---------- Корень маркета ----------

@router.callback_query(F.data == "nav:market")
async def market_home(call: CallbackQuery, state: FSMContext, db_user=None):
    await state.clear()
    lang = _lang(db_user or await get_user(call.from_user.id))
    text = await get_text("market_header", lang)
    try:
        await call.message.edit_text(text, reply_markup=market_root(lang))
    except Exception:
        await call.message.answer(text, reply_markup=market_root(lang))
    await call.answer()


@router.callback_query(F.data == "mkt:rules")
async def market_rules(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await call.message.edit_text(
        await get_text("market_rules", lang),
        reply_markup=back_home(lang),
    )
    await call.answer()


# ---------- Браузинг ----------

@router.callback_query(F.data == "mkt:browse")
async def browse_root(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await call.message.edit_text(
        "<b>📂 Категории</b>\n\n<i>Выберите раздел.</i>",
        reply_markup=market_categories(lang, "browse"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("mkt:browse:"))
async def browse_category(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    cat = call.data.split(":")[2]

    if cat == "vpn":
        await call.message.edit_text(
            await get_text("vpn_wip", lang), reply_markup=market_root(lang))
        await call.answer()
        return

    # 18+ age gate
    if cat == "18plus":
        user = db_user or await get_user(call.from_user.id)
        if not (user and user.get("age_confirmed")):
            await call.message.edit_text(
                await get_text("age_gate", lang),
                reply_markup=age_gate_kb(lang, f"mkt:browse:{cat}"),
            )
            await call.answer()
            return

    await _show_category_first(call, lang, cat)


async def _show_category_first(call: CallbackQuery, lang: str, cat: str):
    items = await list_listings(category=cat, status=L_ACTIVE, limit=50)
    if not items:
        await call.message.edit_text(
            t("market_empty", lang),
            reply_markup=market_categories(lang, "browse"),
        )
        return
    await _show_listing(call, lang, cat, items, 0, items[0]["id"])


async def _show_listing(call_or_msg, lang: str, cat: str, items: list[dict],
                         idx: int, listing_id: int):
    listing = await get_listing(listing_id)
    if not listing or listing["status"] != L_ACTIVE:
        # Объявление сняли — пробуем следующее
        if idx + 1 < len(items):
            await _show_listing(call_or_msg, lang, cat, items, idx + 1, items[idx + 1]["id"])
        return

    photos = await listing_photos(listing_id)
    text = t("listing_card", lang).format(
        title=listing["title"], price=listing["price"],
        cat=cat_label(cat, lang), desc=listing["description"], id=listing["id"],
    )
    kb = listing_nav(lang, listing_id,
                     has_prev=(idx > 0), has_next=(idx + 1 < len(items)),
                     category=cat)

    msg = call_or_msg.message if isinstance(call_or_msg, CallbackQuery) else call_or_msg
    bot = msg.bot
    chat_id = msg.chat.id

    # Удаляем предыдущее сообщение и шлём новое (фото или текст)
    try:
        await msg.delete()
    except Exception:
        pass

    if photos:
        # Сначала отправим медиагруппу (если фото больше 1) или одно фото с подписью
        if len(photos) > 1:
            media = [InputMediaPhoto(media=p) for p in photos[:10]]
            try:
                await bot.send_media_group(chat_id, media)
            except Exception:
                pass
            await bot.send_message(chat_id, text, reply_markup=kb)
        else:
            await bot.send_photo(chat_id, photos[0], caption=text, reply_markup=kb)
    else:
        await bot.send_message(chat_id, text, reply_markup=kb)


@router.callback_query(F.data.startswith("mkt:nav:"))
async def listing_navigate(call: CallbackQuery, db_user=None):
    _, _, cat, direction, current_id = call.data.split(":")
    lang = _lang(db_user or await get_user(call.from_user.id))
    items = await list_listings(category=cat, status=L_ACTIVE, limit=50)
    if not items:
        await call.answer()
        return
    ids = [i["id"] for i in items]
    try:
        cur_idx = ids.index(int(current_id))
    except ValueError:
        cur_idx = 0
    new_idx = cur_idx + 1 if direction == "next" else cur_idx - 1
    new_idx = max(0, min(new_idx, len(items) - 1))
    await _show_listing(call, lang, cat, items, new_idx, items[new_idx]["id"])
    await call.answer()


# ---------- Подтверждение возраста ----------

@router.callback_query(F.data.startswith("age:yes:"))
async def age_yes(call: CallbackQuery, db_user=None):
    next_cb = call.data.split(":", 2)[2]
    await set_user_field(call.from_user.id, "age_confirmed", 1)
    # Эмулируем переход на исходный callback
    call.data = next_cb  # переиспользуем для browse_category
    if next_cb.startswith("mkt:browse:"):
        await browse_category(call, db_user=db_user)
    else:
        await call.answer()


@router.callback_query(F.data == "age:no")
async def age_no(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await call.answer(t("age_denied", lang), show_alert=True)


# ---------- Создание объявления ----------

@router.callback_query(F.data == "mkt:create")
async def create_choose_cat(call: CallbackQuery, state: FSMContext, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await state.clear()
    await call.message.edit_text(
        await get_text("create_choose_category", lang),
        reply_markup=market_categories(lang, "create"),
    )
    await call.answer()


@router.callback_query(F.data.startswith("mkt:create:"))
async def create_set_category(call: CallbackQuery, state: FSMContext, db_user=None):
    cat = call.data.split(":")[2]
    if cat == "vpn":
        await call.answer("В разработке", show_alert=True)
        return
    lang = _lang(db_user or await get_user(call.from_user.id))

    if cat == "18plus":
        user = db_user or await get_user(call.from_user.id)
        if not (user and user.get("age_confirmed")):
            await call.message.edit_text(
                await get_text("age_gate", lang),
                reply_markup=age_gate_kb(lang, f"mkt:create:{cat}"),
            )
            await call.answer()
            return

    await state.update_data(category=cat, lang=lang, photos=[])
    await state.set_state(ListingCreate.title)
    await call.message.edit_text(
        await get_text("create_ask_title", lang),
        reply_markup=listing_create_cancel(lang),
    )
    await call.answer()


@router.message(ListingCreate.title, F.text)
async def create_title(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if len(text) < 3:
        await message.answer(t("validation_short", lang)); return
    if len(text) > LISTING_TITLE_MAX:
        await message.answer(t("validation_long", lang)); return
    await state.update_data(title=text)
    await state.set_state(ListingCreate.description)
    await message.answer(await get_text("create_ask_desc", lang),
                         reply_markup=listing_create_cancel(lang))


@router.message(ListingCreate.description, F.text)
async def create_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer(t("validation_short", lang)); return
    if len(text) > LISTING_DESC_MAX:
        await message.answer(t("validation_long", lang)); return
    await state.update_data(description=text)
    await state.set_state(ListingCreate.price)
    await message.answer(await get_text("create_ask_price", lang),
                         reply_markup=listing_create_cancel(lang))


@router.message(ListingCreate.price, F.text)
async def create_price(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if len(text) < 1 or len(text) > 50:
        await message.answer(t("validation_short", lang)); return
    await state.update_data(price=text)
    await state.set_state(ListingCreate.photos)
    await message.answer(
        (await get_text("create_ask_photos", lang)).format(n=MAX_LISTING_PHOTOS),
        reply_markup=listing_photos_done(lang, has_photos=False),
    )


@router.message(ListingCreate.photos, F.photo)
async def create_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    photos = data.get("photos", [])
    if len(photos) >= MAX_LISTING_PHOTOS:
        await message.answer(t("files_too_many", lang).format(n=MAX_LISTING_PHOTOS))
        return
    photos.append(message.photo[-1].file_id)
    await state.update_data(photos=photos)
    await message.answer(
        t("files_added", lang).format(n=len(photos)),
        reply_markup=listing_photos_done(lang, has_photos=True),
    )


@router.callback_query(F.data == "mkt:create_photos_done", ListingCreate.photos)
async def create_photos_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    photos = data.get("photos", [])
    preview = (await get_text("create_preview", lang)).format(
        cat=cat_label(data["category"], lang),
        title=data["title"], price=data["price"],
        photos=(str(len(photos)) if photos else ("нет" if lang == "ru" else "none")),
        desc=data["description"],
    )
    await state.set_state(ListingCreate.confirm)
    try:
        await call.message.edit_text(preview, reply_markup=listing_create_confirm(lang))
    except Exception:
        await call.message.answer(preview, reply_markup=listing_create_confirm(lang))
    await call.answer()


@router.callback_query(F.data == "mkt:create_cancel")
async def create_cancel(call: CallbackQuery, state: FSMContext, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await state.clear()
    try:
        await call.message.edit_text(t("order_cancelled", lang),
                                     reply_markup=market_root(lang))
    except Exception:
        await call.message.answer(t("order_cancelled", lang),
                                  reply_markup=market_root(lang))
    await call.answer()


@router.callback_query(F.data == "mkt:create_confirm", ListingCreate.confirm)
async def create_confirm(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    listing_id = await create_listing(
        seller_id=call.from_user.id,
        category=data["category"],
        title=data["title"],
        description=data["description"],
        price=data["price"],
    )
    for fid in data.get("photos", []):
        await add_listing_photo(listing_id, fid)
    await state.clear()

    await call.message.edit_text(
        t("create_sent", lang).format(id=listing_id),
        reply_markup=market_root(lang),
    )
    await call.answer()

    # Уведомление админу + карточка модерации
    try:
        user_link = (f"@{call.from_user.username}" if call.from_user.username
                     else f'<a href="tg://user?id={call.from_user.id}">{call.from_user.full_name}</a>')
        listing = await get_listing(listing_id)
        photos = await listing_photos(listing_id)
        msg = (
            f"🆕 <b>Новое объявление №{listing_id}</b>\n\n"
            f"<b>Категория:</b> {cat_label(data['category'], 'ru')}\n"
            f"<b>Заголовок:</b> {listing['title']}\n"
            f"<b>Цена:</b> {listing['price']}\n"
            f"<b>Фото:</b> {len(photos)}\n\n"
            f"{listing['description']}\n\n"
            f"👤 {user_link}  🆔 <code>{call.from_user.id}</code>"
        )
        if photos:
            if len(photos) > 1:
                media = [InputMediaPhoto(media=p) for p in photos[:10]]
                await bot.send_media_group(ADMIN_ID, media)
            await bot.send_message(ADMIN_ID, msg,
                                   reply_markup=listing_moderate_kb(listing_id))
        else:
            await bot.send_message(ADMIN_ID, msg,
                                   reply_markup=listing_moderate_kb(listing_id))
    except Exception:
        pass


# ---------- Мои объявления ----------

@router.callback_query(F.data == "mkt:mine")
async def mine(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    items = await my_listings(call.from_user.id, limit=20)
    if not items:
        text = "📋 <b>" + ("Мои объявления" if lang == "ru" else "My listings") + "</b>\n\n<i>" + \
               ("Пока пусто." if lang == "ru" else "Empty.") + "</i>"
        try:
            await call.message.edit_text(text, reply_markup=market_root(lang))
        except Exception:
            await call.message.answer(text, reply_markup=market_root(lang))
        await call.answer()
        return

    lines = ["<b>📋 " + ("Мои объявления" if lang == "ru" else "My listings") + "</b>", ""]
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for it in items:
        st = L_LABELS.get(it["status"], it["status"])
        lines.append(f"<b>№{it['id']}</b> · {st}\n▸ {it['title']} — {it['price']}\n")
        kb.button(text=f"№{it['id']} · {it['title'][:24]}",
                  callback_data=f"mkt:my:{it['id']}")
    kb.button(text=t("btn_home", lang), callback_data="nav:home")
    kb.adjust(1)
    try:
        await call.message.edit_text("\n".join(lines), reply_markup=kb.as_markup())
    except Exception:
        await call.message.answer("\n".join(lines), reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("mkt:my:"))
async def my_listing_view(call: CallbackQuery, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    lid = int(call.data.split(":")[2])
    listing = await get_listing(lid)
    if not listing or listing["seller_id"] != call.from_user.id:
        await call.answer("Не найдено", show_alert=True); return
    st = L_LABELS.get(listing["status"], listing["status"])
    text = (
        f"<b>№{listing['id']}</b> · {st}\n"
        f"<b>{listing['title']}</b>\n"
        f"💰 {listing['price']}\n\n"
        f"{listing['description']}"
    )
    try:
        await call.message.edit_text(text, reply_markup=my_listing_actions(lang, lid))
    except Exception:
        await call.message.answer(text, reply_markup=my_listing_actions(lang, lid))
    await call.answer()


@router.callback_query(F.data.startswith("mkt:sold:"))
async def mark_sold(call: CallbackQuery):
    lid = int(call.data.split(":")[2])
    listing = await get_listing(lid)
    if not listing or listing["seller_id"] != call.from_user.id:
        await call.answer(); return
    await set_listing_status(lid, L_SOLD)
    await call.answer("Отмечено как продано", show_alert=True)
    await mine(call)


@router.callback_query(F.data.startswith("mkt:remove:"))
async def mark_removed(call: CallbackQuery):
    lid = int(call.data.split(":")[2])
    listing = await get_listing(lid)
    if not listing or listing["seller_id"] != call.from_user.id:
        await call.answer(); return
    await set_listing_status(lid, L_REMOVED)
    await call.answer("Снято", show_alert=True)
    await mine(call)


# ---------- Анонимный чат покупатель ↔ продавец ----------

async def _start_chat(bot, lang_buyer, lang_seller, buyer_state, listing,
                       buyer_id, seller_id):
    await buyer_state.set_state(P2PChat.chatting)
    await buyer_state.update_data(partner_id=seller_id, listing_id=listing["id"])
    # Уведомление покупателю
    await bot.send_message(
        buyer_id, t("chat_started", lang_buyer).format(id=listing["id"]),
        reply_markup=chat_kb(lang_buyer))
    # Уведомление продавцу + ставим ему такое же состояние
    # Состояние продавцу установим лениво: при первом сообщении пары
    # будем хранить активные пары в settings (chat:<a>:<b>) для проверки
    pair_key = f"chat:{min(buyer_id, seller_id)}:{max(buyer_id, seller_id)}"
    from database import set_setting
    await set_setting(pair_key, f"{listing['id']}:{seller_id}")  # хранит who is seller
    await bot.send_message(
        seller_id,
        t("chat_started_seller", lang_seller).format(id=listing["id"]),
        reply_markup=chat_kb(lang_seller))


@router.callback_query(F.data.startswith("mkt:buy:"))
async def start_chat(call: CallbackQuery, state: FSMContext, bot: Bot,
                      db_user=None):
    lid = int(call.data.split(":")[2])
    listing = await get_listing(lid)
    if not listing or listing["status"] != L_ACTIVE:
        await call.answer("Объявление недоступно", show_alert=True); return
    if listing["seller_id"] == call.from_user.id:
        await call.answer("Это ваше объявление", show_alert=True); return

    lang_buyer = _lang(db_user or await get_user(call.from_user.id))
    seller = await get_user(listing["seller_id"])
    lang_seller = (seller and seller.get("language")) or "ru"

    await _start_chat(bot, lang_buyer, lang_seller, state, listing,
                      call.from_user.id, listing["seller_id"])
    await call.answer()


@router.message(P2PChat.chatting)
async def relay_msg(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    partner = data.get("partner_id")
    lid = data.get("listing_id")
    if not partner:
        return
    try:
        await bot.send_message(
            partner, t("chat_msg_intro", "ru").format(id=lid),
        )
        await bot.copy_message(partner, message.chat.id, message.message_id)
        await message.reply(t("chat_delivered", "ru"))
    except Exception:
        await message.reply(t("chat_failed", "ru"))


@router.callback_query(F.data == "mkt:chat_stop")
async def chat_stop(call: CallbackQuery, state: FSMContext, bot: Bot,
                    db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    data = await state.get_data()
    partner = data.get("partner_id")
    await state.clear()
    await call.message.answer(t("chat_ended", lang), reply_markup=main_menu(lang))
    if partner:
        try:
            await bot.send_message(partner, t("chat_partner_left", "ru"))
        except Exception:
            pass
    # Удалим pair settings, если есть
    if partner:
        from database import set_setting
        a, b = sorted([call.from_user.id, partner])
        await set_setting(f"chat:{a}:{b}", None)
    await call.answer()

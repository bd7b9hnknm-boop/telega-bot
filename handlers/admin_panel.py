# Объединённая админ-панель: /panel
# Разделы: тексты, фото, маркет-модерация, исполнители, документы,
# общежитие, воспитатели, реквизиты оплаты, ЧС, статистика.
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import (
    get_setting, set_setting,
    list_blocked, unblock_user, get_stats,
    pending_listings, get_listing, listing_photos, set_listing_status,
    add_provider, update_provider, delete_provider, list_providers, get_provider,
    add_document, list_documents, get_document, delete_document,
    add_supervisor, list_supervisors, delete_supervisor, update_supervisor,
    get_supervisor, log_duty, get_duty_state, set_duty_state,
    L_ACTIVE, L_REJECTED,
)
from keyboards.admin import (
    panel_root, texts_menu, text_lang_choice, cancel_edit,
    photo_menu, blocked_list_kb, EDITABLE_TEXTS,
    market_admin_root, listing_moderate_kb,
    providers_admin, provider_edit_kb,
    documents_admin, document_item_kb,
    dorm_admin, supervisors_admin, supervisor_item_kb, floor_choice_for_sup,
    payments_admin, schedule_admin,
)
from database import all_subscribed_groups, latest_snapshot
from integrations import ttzht
from handlers.schedule_poller import check_once
from utils.i18n import t
from states.admin import (
    AdminEdit, AdminProvider, AdminDoc, AdminSupervisor, AdminDormChat,
)
from integrations import cryptobot
from handlers.marketplace import cat_label
from handlers.dorm import resolve_duty_for_today, render_duty

router = Router()


def _admin(uid) -> bool:
    return uid == ADMIN_ID


# ---------- Вход ----------

@router.message(Command("panel", "admin"))
async def open_panel(message: Message, state: FSMContext):
    if not _admin(message.from_user.id):
        return
    await state.clear()
    await message.answer("<b>🛠 Панель администратора</b>", reply_markup=panel_root())


@router.callback_query(F.data == "pnl:home")
async def panel_home(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await state.clear()
    try:
        await call.message.edit_text("<b>🛠 Панель администратора</b>",
                                     reply_markup=panel_root())
    except Exception:
        await call.message.answer("<b>🛠 Панель администратора</b>",
                                  reply_markup=panel_root())
    await call.answer()


@router.callback_query(F.data == "pnl:close")
async def panel_close(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer("Закрыто")


# ---------- Статистика ----------

@router.callback_query(F.data == "pnl:stats")
async def panel_stats(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    s = await get_stats()
    text = (
        "<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{s['users']}</b>\n"
        f"🚫 В ЧС: <b>{s['blocked']}</b>\n"
        f"📦 Заявок всего: <b>{s['total']}</b>\n"
        f"  🟡 {s['pending']}  🟢 {s['accepted']}  ✅ {s['completed']}  🔴 {s['rejected']}\n\n"
        f"🛒 Объявлений активных: <b>{s['listings_active']}</b>\n"
        f"⏳ На модерации: <b>{s['listings_pending']}</b>"
    )
    await call.message.edit_text(text, reply_markup=panel_root())
    await call.answer()


# ---------- Тексты ----------

@router.callback_query(F.data == "pnl:texts")
async def panel_texts(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await call.message.edit_text(
        "<b>📝 Редактор текстов</b>\n\nВыберите фрагмент.",
        reply_markup=texts_menu())
    await call.answer()


@router.callback_query(F.data.startswith("pnl:txt:"))
async def panel_text_choose(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    key = call.data.split(":", 2)[2]
    label = dict(EDITABLE_TEXTS).get(key, key)

    def _short(s):
        s = (s or "").replace("\n", " ")
        return s[:200] + ("…" if len(s) > 200 else "")

    ru_cur = await get_setting(f"text:ru:{key}") or t(key, "ru")
    en_cur = await get_setting(f"text:en:{key}") or t(key, "en")
    text = (
        f"<b>{label}</b>\n\n"
        f"<b>🇷🇺 RU:</b> <i>{_short(ru_cur)}</i>\n\n"
        f"<b>🇬🇧 EN:</b> <i>{_short(en_cur)}</i>"
    )
    await call.message.edit_text(text, reply_markup=text_lang_choice(key))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:edit:"))
async def panel_text_edit(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    _, _, key, lang = call.data.split(":")
    await state.set_state(AdminEdit.waiting_text)
    await state.update_data(edit_key=key, edit_lang=lang)
    label = dict(EDITABLE_TEXTS).get(key, key)
    await call.message.edit_text(
        f"✏️ <b>Новый текст для «{label}» ({lang.upper()})</b>\n\n"
        "HTML поддерживается. В welcome используйте {name}.",
        reply_markup=cancel_edit())
    await call.answer()


@router.message(AdminEdit.waiting_text, F.text)
async def admin_edit_save(message: Message, state: FSMContext):
    """Единый диспетчер сохранения текста: тексты, поля исполнителей,
    общага, реквизиты — определяется по содержимому state."""
    if not _admin(message.from_user.id):
        return
    data = await state.get_data()
    val = message.html_text

    if data.get("prov_field"):
        field = data["prov_field"]; pid = data["prov_id"]
        plain = message.text.strip()
        await update_provider(pid, **{field: (None if plain == "-" else plain[:200])})
        await state.clear()
        await message.answer("✅ Поле обновлено.", reply_markup=panel_root())
        return

    if data.get("dorm_key"):
        await set_setting(data["dorm_key"], val)
        await state.clear()
        await message.answer("✅ Сохранено.", reply_markup=panel_root())
        return

    if data.get("pay_key"):
        await set_setting(data["pay_key"], val)
        await state.clear()
        await message.answer("✅ Реквизиты сохранены.", reply_markup=panel_root())
        return

    key, lang = data.get("edit_key"), data.get("edit_lang")
    if key and lang:
        await set_setting(f"text:{lang}:{key}", val)
        await state.clear()
        await message.answer(f"✅ Сохранено ({lang.upper()}: {key}).",
                             reply_markup=panel_root())
        return

    await state.clear()


@router.callback_query(F.data.startswith("pnl:reset:"))
async def panel_text_reset(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    key = call.data.split(":", 2)[2]
    await set_setting(f"text:ru:{key}", None)
    await set_setting(f"text:en:{key}", None)
    await call.answer("Сброшено", show_alert=True)
    await call.message.edit_text("<b>📝 Редактор текстов</b>",
                                 reply_markup=texts_menu())


# ---------- Фото ----------

@router.callback_query(F.data == "pnl:photo")
async def panel_photo(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    photo_id = await get_setting("welcome_photo")
    text = ("<b>🖼 Приветственное фото</b>\n\n" +
            ("✅ Установлено." if photo_id else "❌ Не установлено."))
    await call.message.edit_text(text, reply_markup=photo_menu(bool(photo_id)))
    await call.answer()


@router.callback_query(F.data == "pnl:photo_set")
async def panel_photo_set(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await state.set_state(AdminEdit.waiting_photo)
    await call.message.edit_text(
        "📤 Отправьте фотографию следующим сообщением.",
        reply_markup=cancel_edit())
    await call.answer()


@router.message(AdminEdit.waiting_photo, F.photo)
async def panel_photo_save(message: Message, state: FSMContext):
    if not _admin(message.from_user.id):
        return
    await set_setting("welcome_photo", message.photo[-1].file_id)
    await state.clear()
    await message.answer("✅ Фото обновлено.", reply_markup=panel_root())


@router.callback_query(F.data == "pnl:photo_del")
async def panel_photo_del(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await set_setting("welcome_photo", None)
    await call.message.edit_text("🗑 Удалено.", reply_markup=panel_root())
    await call.answer()


# ---------- ЧС ----------

async def _render_blocked(call: CallbackQuery):
    users = await list_blocked(limit=30)
    if not users:
        await call.message.edit_text("<b>🚫 ЧС</b>\n\n<i>Пусто.</i>",
                                     reply_markup=panel_root())
        return
    lines = ["<b>🚫 Чёрный список</b>", ""]
    for u in users:
        uname = f"@{u['username']}" if u["username"] else (u["full_name"] or "—")
        reason = u.get("block_reason") or "—"
        lines.append(f"▸ <code>{u['id']}</code> {uname} · {reason}")
    await call.message.edit_text("\n".join(lines),
                                 reply_markup=blocked_list_kb(users))


@router.callback_query(F.data == "pnl:blocked")
async def panel_blocked(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await _render_blocked(call); await call.answer()


@router.callback_query(F.data.startswith("pnl:unblock:"))
async def panel_unblock(call: CallbackQuery, bot: Bot):
    if not _admin(call.from_user.id):
        await call.answer(); return
    uid = int(call.data.split(":")[2])
    await unblock_user(uid)
    try:
        await bot.send_message(uid,
            "✅ Доступ восстановлен. Отправьте /start.")
    except Exception:
        pass
    await call.answer("Разблокирован", show_alert=True)
    await _render_blocked(call)


# ============================================================
# Маркет — модерация
# ============================================================

@router.callback_query(F.data == "pnl:market")
async def panel_market(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await call.message.edit_text(
        "<b>🛒 Маркет — модерация</b>", reply_markup=market_admin_root())
    await call.answer()


@router.callback_query(F.data == "pnl:mkt:queue")
async def market_queue(call: CallbackQuery, bot: Bot):
    if not _admin(call.from_user.id):
        await call.answer(); return
    items = await pending_listings(limit=20)
    if not items:
        await call.message.edit_text(
            "<b>📥 Очередь модерации</b>\n\n<i>Нет объявлений.</i>",
            reply_markup=market_admin_root())
        await call.answer(); return

    # Покажем первое в очереди
    listing = items[0]
    photos = await listing_photos(listing["id"])
    user_link = (f"@{listing['username']}" if listing.get("username")
                 else f'<a href="tg://user?id={listing["seller_id"]}">{listing["full_name"]}</a>')
    text = (
        f"📥 <b>Объявление №{listing['id']}</b> ({len(items)} в очереди)\n\n"
        f"<b>Категория:</b> {cat_label(listing['category'], 'ru')}\n"
        f"<b>Заголовок:</b> {listing['title']}\n"
        f"<b>Цена:</b> {listing['price']}\n"
        f"<b>Фото:</b> {len(photos)}\n\n"
        f"{listing['description']}\n\n"
        f"👤 {user_link}"
    )
    try:
        await call.message.delete()
    except Exception:
        pass
    if photos and len(photos) > 1:
        await bot.send_media_group(call.from_user.id,
            [InputMediaPhoto(media=p) for p in photos[:10]])
    if photos:
        await bot.send_photo(call.from_user.id, photos[0],
            caption=text, reply_markup=listing_moderate_kb(listing["id"]))
    else:
        await bot.send_message(call.from_user.id, text,
            reply_markup=listing_moderate_kb(listing["id"]))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:mkt:ok:"))
async def market_ok(call: CallbackQuery, bot: Bot):
    if not _admin(call.from_user.id):
        await call.answer(); return
    lid = int(call.data.split(":")[3])
    await set_listing_status(lid, L_ACTIVE)
    listing = await get_listing(lid)
    if listing:
        try:
            await bot.send_message(listing["seller_id"],
                f"✅ <b>Ваше объявление №{lid} опубликовано.</b>")
        except Exception:
            pass
    await call.answer("Опубликовано", show_alert=True)
    await market_queue(call, bot)


@router.callback_query(F.data.startswith("pnl:mkt:no:"))
async def market_no(call: CallbackQuery, bot: Bot):
    if not _admin(call.from_user.id):
        await call.answer(); return
    lid = int(call.data.split(":")[3])
    await set_listing_status(lid, L_REJECTED)
    listing = await get_listing(lid)
    if listing:
        try:
            await bot.send_message(listing["seller_id"],
                f"🔴 <b>Ваше объявление №{lid} отклонено.</b>\n"
                "Уточните детали в поддержке.")
        except Exception:
            pass
    await call.answer("Отклонено", show_alert=True)
    await market_queue(call, bot)


# ============================================================
# Исполнители (распечатка / конспекты)
# ============================================================

PROV_FIELD_TITLES = {
    "name": "ФИО / Имя",
    "room": "Комната",
    "contact": "Контакт",
    "price_info": "Цены",
    "note": "Заметка",
}


@router.callback_query(F.data.startswith("pnl:srv:"))
async def panel_service(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    service = call.data.split(":")[2]
    providers = await list_providers(service, only_active=False)
    title = "🖨 Распечатка" if service == "print" else "📝 Конспекты"
    await call.message.edit_text(
        f"<b>{title}</b>\n\n<i>Список исполнителей.</i>",
        reply_markup=providers_admin(service, providers))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:prov:add:"))
async def prov_add(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    service = call.data.split(":")[3]
    await state.set_state(AdminProvider.name)
    await state.update_data(service=service)
    await call.message.edit_text(
        "✏️ Введите <b>ФИО / имя</b> исполнителя:",
        reply_markup=cancel_edit())
    await call.answer()


@router.message(AdminProvider.name, F.text)
async def prov_set_name(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    await state.update_data(name=message.text.strip()[:80])
    await state.set_state(AdminProvider.room)
    await message.answer("🚪 Введите номер <b>комнаты</b> (или «-»):",
                         reply_markup=cancel_edit())


@router.message(AdminProvider.room, F.text)
async def prov_set_room(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    room = message.text.strip()
    await state.update_data(room=None if room == "-" else room[:40])
    await state.set_state(AdminProvider.contact)
    await message.answer("📱 Контакт (например, @username или «-»):",
                         reply_markup=cancel_edit())


@router.message(AdminProvider.contact, F.text)
async def prov_set_contact(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    c = message.text.strip()
    await state.update_data(contact=None if c == "-" else c[:80])
    await state.set_state(AdminProvider.price)
    await message.answer("💰 Цены (свободный текст или «-»):",
                         reply_markup=cancel_edit())


@router.message(AdminProvider.price, F.text)
async def prov_set_price(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    p = message.text.strip()
    await state.update_data(price_info=None if p == "-" else p[:200])
    await state.set_state(AdminProvider.note)
    await message.answer("📝 Заметка (или «-»):", reply_markup=cancel_edit())


@router.message(AdminProvider.note, F.text)
async def prov_set_note(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    n = message.text.strip()
    data = await state.get_data()
    await state.clear()
    await add_provider(
        service=data["service"], name=data["name"],
        room=data.get("room"), contact=data.get("contact"),
        price_info=data.get("price_info"),
        note=None if n == "-" else n[:200],
    )
    await message.answer("✅ Исполнитель добавлен.", reply_markup=panel_root())


@router.callback_query(F.data.startswith("pnl:prov:edit:"))
async def prov_edit(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    pid = int(call.data.split(":")[3])
    p = await get_provider(pid)
    if not p:
        await call.answer("Не найдено"); return
    text = (
        f"<b>{p['name']}</b>\n"
        f"🚪 {p.get('room') or '—'}\n"
        f"📱 {p.get('contact') or '—'}\n"
        f"💰 {p.get('price_info') or '—'}\n"
        f"📝 {p.get('note') or '—'}\n\n"
        f"Статус: {'🟢 активен' if p['is_active'] else '🔕 скрыт'}"
    )
    await call.message.edit_text(text,
        reply_markup=provider_edit_kb(pid, bool(p["is_active"]), p["service"]))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:prov:toggle:"))
async def prov_toggle(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    pid = int(call.data.split(":")[3])
    p = await get_provider(pid)
    if not p:
        await call.answer(); return
    await update_provider(pid, is_active=0 if p["is_active"] else 1)
    await call.answer("Изменено")
    await prov_edit(call)


@router.callback_query(F.data.startswith("pnl:prov:del:"))
async def prov_del(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    pid = int(call.data.split(":")[3])
    p = await get_provider(pid)
    await delete_provider(pid)
    await call.answer("Удалено", show_alert=True)
    if p:
        # Возврат к списку
        providers = await list_providers(p["service"], only_active=False)
        title = "🖨 Распечатка" if p["service"] == "print" else "📝 Конспекты"
        await call.message.edit_text(
            f"<b>{title}</b>",
            reply_markup=providers_admin(p["service"], providers))


@router.callback_query(F.data.startswith("pnl:prov:f:"))
async def prov_field_edit(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    _, _, _, pid, field = call.data.split(":")
    await state.set_state(AdminEdit.waiting_text)
    await state.update_data(prov_field=field, prov_id=int(pid))
    await call.message.edit_text(
        f"✏️ Новое значение поля «{PROV_FIELD_TITLES.get(field, field)}» "
        "(или «-» чтобы очистить):",
        reply_markup=cancel_edit())
    await call.answer()


# prov_field обрабатывается в admin_edit_save


# ============================================================
# Документы
# ============================================================

@router.callback_query(F.data == "pnl:docs")
async def panel_docs(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    docs = await list_documents()
    await call.message.edit_text(
        "<b>📋 Документы (шаблоны)</b>\n\n<i>Список ниже. Нажмите для редактирования.</i>",
        reply_markup=documents_admin(docs))
    await call.answer()


@router.callback_query(F.data == "pnl:docs:add")
async def doc_add(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await state.set_state(AdminDoc.title)
    await call.message.edit_text(
        "✏️ Введите <b>название документа</b> (например, «Заявление на пропуск»):",
        reply_markup=cancel_edit())
    await call.answer()


@router.message(AdminDoc.title, F.text)
async def doc_title(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    await state.update_data(title=message.text.strip()[:100])
    await state.set_state(AdminDoc.file)
    await message.answer(
        "📎 Прикрепите <b>файл</b> документа (любой формат: pdf, docx, jpg…).",
        reply_markup=cancel_edit())


@router.message(AdminDoc.file)
async def doc_file(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    file_id = None; file_type = None
    if message.document:
        file_id = message.document.file_id; file_type = "document"
    elif message.photo:
        file_id = message.photo[-1].file_id; file_type = "photo"
    if not file_id:
        await message.answer("⚠️ Прикрепите файл документом или фото.")
        return
    data = await state.get_data()
    await add_document(title=data["title"], file_id=file_id, file_type=file_type)
    await state.clear()
    await message.answer("✅ Документ добавлен.", reply_markup=panel_root())


@router.callback_query(F.data.startswith("pnl:docs:item:"))
async def doc_item(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    did = int(call.data.split(":")[3])
    d = await get_document(did)
    if not d:
        await call.answer(); return
    await call.message.edit_text(
        f"<b>📄 {d['title']}</b>\n\nДобавлен: {d['created_at'][:10]}",
        reply_markup=document_item_kb(did))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:docs:del:"))
async def doc_del(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    did = int(call.data.split(":")[3])
    await delete_document(did)
    await call.answer("Удалён", show_alert=True)
    docs = await list_documents()
    await call.message.edit_text("<b>📋 Документы</b>",
                                 reply_markup=documents_admin(docs))


# ============================================================
# Общежитие
# ============================================================

DORM_FIELD_PROMPTS = {
    "pay_text": ("💰 Введите текст «Оплата проживания» (HTML, RU). "
                 "Можете задать английский через ключ pay_text:en.",
                 "dorm:pay_text:ru"),
    "pay_link": ("🔗 Введите URL для кнопки «Перейти к оплате (Сбер)». "
                 "Если оплачиваем по QR — вставьте сюда ссылку из приложения.",
                 "dorm:pay_link"),
    "info":     ("ℹ️ Введите текст полезной информации (HTML, RU).",
                 "dorm:info:ru"),
}


@router.callback_query(F.data == "pnl:dorm")
async def panel_dorm(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    chat_id_set = await get_setting("dorm:chat_id")
    extra = (f"\n\n💬 Чат для рассылки: <code>{chat_id_set}</code>" if chat_id_set
             else "\n\n💬 Чат для рассылки не задан.")
    await call.message.edit_text(
        f"<b>🏠 Общежитие</b>{extra}",
        reply_markup=dorm_admin())
    await call.answer()


@router.callback_query(F.data.startswith("pnl:dorm:edit:"))
async def dorm_edit(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    field = call.data.split(":")[3]
    if field == "chat_id":
        await state.set_state(AdminDormChat.waiting)
        await call.message.edit_text(
            "💬 Введите <code>chat_id</code> чата общаги для рассылок дежурств.\n\n"
            "<i>Можно узнать так: добавьте бота в чат, отправьте там /chatid — "
            "получите id.</i>",
            reply_markup=cancel_edit())
        await call.answer(); return

    prompt, key = DORM_FIELD_PROMPTS[field]
    await state.set_state(AdminEdit.waiting_text)
    await state.update_data(dorm_key=key)
    await call.message.edit_text(prompt, reply_markup=cancel_edit())
    await call.answer()


# dorm обрабатывается в admin_edit_save


@router.message(AdminDormChat.waiting, F.text)
async def dorm_chat_save(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    val = message.text.strip()
    try:
        int(val)
    except ValueError:
        await message.answer("⚠️ chat_id должен быть числом (можно отрицательным)."); return
    await set_setting("dorm:chat_id", val)
    await state.clear()
    await message.answer(f"✅ Чат общаги: <code>{val}</code>.",
                         reply_markup=panel_root())


# Команда /chatid для добавления в чат, чтобы узнать id
@router.message(Command("chatid"))
async def cmd_chatid(message: Message):
    """В чате бот говорит id чата (видит только админ)."""
    if message.from_user.id != ADMIN_ID:
        return
    await message.reply(f"chat_id: <code>{message.chat.id}</code>")


# ============================================================
# Воспитатели
# ============================================================

@router.callback_query(F.data == "pnl:sup")
async def panel_sup(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    sup = await list_supervisors(only_active=False)
    by_floor = {0: [], 2: [], 3: []}
    for s in sup:
        by_floor.setdefault(s["floor"], []).append(s)
    await call.message.edit_text(
        "<b>👤 Воспитатели</b>\n\n"
        "<i>⭐ — главный (с утра до обеда)</i>\n"
        "<i>2э / 3э — этажи</i>",
        reply_markup=supervisors_admin(by_floor))
    await call.answer()


@router.callback_query(F.data == "pnl:sup:add")
async def sup_add(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await state.set_state(AdminSupervisor.name)
    await call.message.edit_text("✏️ ФИО воспитателя:", reply_markup=cancel_edit())
    await call.answer()


@router.message(AdminSupervisor.name, F.text)
async def sup_name(message: Message, state: FSMContext):
    if not _admin(message.from_user.id): return
    await state.update_data(name=message.text.strip()[:100])
    await state.set_state(AdminSupervisor.floor)
    await message.answer("🏢 Выберите этаж:", reply_markup=floor_choice_for_sup())


@router.callback_query(F.data.startswith("pnl:sup:floor:"), AdminSupervisor.floor)
async def sup_floor(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    floor = int(call.data.split(":")[3])
    data = await state.get_data()
    await add_supervisor(full_name=data["name"], floor=floor)
    await state.clear()
    await call.message.edit_text(f"✅ Добавлен: {data['name']} (этаж {floor or 'главный'}).",
                                 reply_markup=panel_root())
    await call.answer()


@router.callback_query(F.data.startswith("pnl:sup:edit:"))
async def sup_edit(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    sid = int(call.data.split(":")[3])
    s = await get_supervisor(sid)
    if not s:
        await call.answer(); return
    floor = "главный" if s["floor"] == 0 else f"{s['floor']} этаж"
    await call.message.edit_text(
        f"<b>{s['full_name']}</b>\n\nЭтаж: {floor}\nПозиция: {s['position']}",
        reply_markup=supervisor_item_kb(sid))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:sup:del:"))
async def sup_del(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    sid = int(call.data.split(":")[3])
    await delete_supervisor(sid)
    await call.answer("Удалён", show_alert=True)
    await panel_sup(call)


@router.callback_query(F.data.startswith("pnl:sup:next:"))
async def sup_next(call: CallbackQuery):
    """Сдвинуть очередь на следующего и перезаписать сегодняшнего."""
    if not _admin(call.from_user.id):
        await call.answer(); return
    floor = int(call.data.split(":")[3])
    sup_list = await list_supervisors(floor=floor, only_active=True)
    if not sup_list:
        await call.answer("Нет активных", show_alert=True); return
    st = await get_duty_state(floor)
    new_idx = (st["current_index"] + 1) % len(sup_list)
    await set_duty_state(floor, new_idx, st["last_shift_date"])
    # Перезаписываем сегодняшнего
    from handlers.dorm import today_local
    today = today_local()
    chosen = sup_list[new_idx]
    await log_duty(today, floor, chosen["id"], chosen["full_name"], is_skip=False)
    await call.answer(f"Теперь дежурит: {chosen['full_name']}", show_alert=True)
    await panel_sup(call)


@router.callback_query(F.data.startswith("pnl:sup:skip:"))
async def sup_skip(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    floor = int(call.data.split(":")[3])
    from handlers.dorm import today_local
    today = today_local()
    await log_duty(today, floor, None, None, is_skip=True)
    await call.answer("Выходной отмечен", show_alert=True)
    await panel_sup(call)


@router.callback_query(F.data == "pnl:sup:today")
async def sup_today(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    d = await resolve_duty_for_today()
    await call.message.edit_text(render_duty(d, "ru"), reply_markup=panel_root())
    await call.answer()


@router.callback_query(F.data == "pnl:sup:broadcast")
async def sup_broadcast(call: CallbackQuery, bot: Bot):
    if not _admin(call.from_user.id):
        await call.answer(); return
    chat_id = await get_setting("dorm:chat_id")
    if not chat_id:
        await call.answer("chat_id не задан", show_alert=True); return
    d = await resolve_duty_for_today()
    try:
        await bot.send_message(int(chat_id), render_duty(d, "ru"))
        await call.answer("Отправлено", show_alert=True)
    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)


# ============================================================
# Реквизиты оплат
# ============================================================

@router.callback_query(F.data == "pnl:pay")
async def panel_pay(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    card = await get_setting("pay:card_requisites")
    has_card = bool(card and card.strip())
    has_crypto = cryptobot.is_enabled()
    text = (
        "<b>💳 Реквизиты для оплат</b>\n\n"
        f"▸ Карта/СБП: {'✅ настроены' if has_card else '❌ не заданы'}\n"
        f"▸ CryptoBot: {'✅ токен задан' if has_crypto else '❌ токен отсутствует'}\n\n"
        "<i>Сумму конкретной заявки можно задать командой:</i>\n"
        "<code>/setamount &lt;order_id&gt; &lt;сумма_₽&gt;</code>\n"
        "<code>/setusdt &lt;order_id&gt; &lt;сумма_USDT&gt;</code>"
    )
    await call.message.edit_text(text, reply_markup=payments_admin(has_card, has_crypto))
    await call.answer()


@router.callback_query(F.data == "pnl:pay:edit:card")
async def panel_pay_card_edit(call: CallbackQuery, state: FSMContext):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await state.set_state(AdminEdit.waiting_text)
    await state.update_data(pay_key="pay:card_requisites")
    cur = await get_setting("pay:card_requisites") or "—"
    await call.message.edit_text(
        f"✏️ Введите <b>реквизиты карты</b> (HTML).\n\n"
        f"Сейчас: <blockquote>{cur}</blockquote>",
        reply_markup=cancel_edit())
    await call.answer()


@router.callback_query(F.data == "pnl:pay:info")
async def panel_pay_crypto_info(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await call.message.edit_text(
        "<b>🪙 CryptoBot</b>\n\n"
        "Токен задаётся переменной окружения <code>CRYPTOBOT_TOKEN</code> "
        "(Railway → Variables).\n\n"
        "1. Откройте @CryptoBot → Crypto Pay → Create App\n"
        "2. Скопируйте API Token\n"
        "3. Вставьте в Railway Variables\n"
        "4. Передеплойте бот",
        reply_markup=payments_admin(False, cryptobot.is_enabled()))
    await call.answer()


# /setamount и /setusdt
@router.message(Command("setamount"))
async def cmd_setamount(message: Message):
    if not _admin(message.from_user.id): return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: <code>/setamount &lt;order_id&gt; &lt;сумма&gt;</code>")
        return
    try:
        oid = int(parts[1])
    except ValueError:
        await message.answer("order_id должен быть числом."); return
    await set_setting(f"order_amount:{oid}", parts[2])
    await message.answer(f"✅ Сумма по заявке №{oid}: <b>{parts[2]}</b>")


@router.message(Command("setusdt"))
async def cmd_setusdt(message: Message):
    if not _admin(message.from_user.id): return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: <code>/setusdt &lt;order_id&gt; &lt;USDT&gt;</code>")
        return
    try:
        oid = int(parts[1]); float(parts[2])
    except ValueError:
        await message.answer("Неверные параметры."); return
    await set_setting(f"order_amount_usdt:{oid}", parts[2])
    await message.answer(f"✅ Сумма USDT по заявке №{oid}: <b>{parts[2]}</b>")


# pay_key обрабатывается в admin_edit_save


# ============================================================
# Замены ТТЖТ
# ============================================================

@router.callback_query(F.data == "pnl:sched")
async def panel_sched(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    enabled = (await get_setting("sched:enabled")) != "0"
    has_chat = bool(await get_setting("dorm:chat_id"))
    snap = await latest_snapshot()
    last_str = ("—" if not snap else snap["fetched_at"][:16].replace("T", " "))
    total_subs = sum((await all_subscribed_groups()).values())
    await call.message.edit_text(
        "<b>📅 Замены ТТЖТ</b>\n\n"
        f"Источник: <code>{ttzht.SOURCE_URL}</code>\n"
        f"Последняя проверка: <code>{last_str}</code> UTC\n"
        f"Подписок всего: <b>{total_subs}</b>\n\n"
        "<i>В часы 11–17 (Томск) — опрос каждые 10 мин, в остальное "
        "время — раз в час. Ночью спит.</i>",
        reply_markup=schedule_admin(enabled, has_chat))
    await call.answer()


@router.callback_query(F.data == "pnl:sched:toggle")
async def sched_toggle(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    cur = (await get_setting("sched:enabled")) != "0"
    await set_setting("sched:enabled", "0" if cur else "1")
    await call.answer("Переключено")
    await panel_sched(call)


@router.callback_query(F.data == "pnl:sched:run")
async def sched_run(call: CallbackQuery, bot: Bot):
    if not _admin(call.from_user.id):
        await call.answer(); return
    await call.answer("Запускаю…")
    res = await check_once(bot)
    if not res.get("ok"):
        msg = f"⚠️ Ошибка: {res.get('reason')}"
    else:
        ch = "есть, рассылка отправлена" if res.get("changed") else "нет"
        msg = f"✅ Проверено. Изменения: {ch}. Дней: {res.get('days', '—')}."
    await call.message.answer(msg, reply_markup=panel_root())


@router.callback_query(F.data == "pnl:sched:snap")
async def sched_snap(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    snap = await latest_snapshot()
    if not snap:
        await call.message.edit_text("<i>Снимков ещё нет.</i>",
                                     reply_markup=schedule_admin(True, True))
        await call.answer(); return
    days = ttzht.from_json(snap["payload"])
    text = ttzht.render_full(days, limit_rows=50)
    if len(text) > 3800:
        text = text[:3800] + "\n\n<i>…сокращено</i>"
    await call.message.edit_text(
        f"<b>📋 Последний снимок</b> ({snap['fetched_at'][:16].replace('T', ' ')} UTC)\n\n{text}",
        reply_markup=schedule_admin(True, True))
    await call.answer()


@router.callback_query(F.data == "pnl:sched:subs")
async def sched_subs(call: CallbackQuery):
    if not _admin(call.from_user.id):
        await call.answer(); return
    data = await all_subscribed_groups()
    if not data:
        text = "<i>Подписок пока нет.</i>"
    else:
        lines = ["<b>👥 Подписчики по группам</b>", ""]
        for g, n in data.items():
            lines.append(f"▸ <b>{g}</b> — {n}")
        text = "\n".join(lines)
    await call.message.edit_text(text, reply_markup=schedule_admin(True, True))
    await call.answer()

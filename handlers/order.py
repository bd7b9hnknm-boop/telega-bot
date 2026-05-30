# FSM заказа: категория → задача → срок → вложения → подтверждение
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID, MAX_ATTACHMENTS
from database import (
    has_pending_order, create_order, count_completed_orders,
    add_attachment, get_user,
)
from utils.catalog import CATALOG, category_title
from utils.i18n import t, get_text
from keyboards.inline import (
    choose_category, order_cancel, order_confirm, attach_kb, main_menu,
    admin_order_actions,
)
from states.order import OrderForm

MAX_TASK_LEN = 1500
MAX_DEADLINE_LEN = 100

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


# ---------- Старт ----------

@router.callback_query(F.data == "order:choose")
async def order_choose(call: CallbackQuery, state: FSMContext, db_user=None):
    await state.clear()
    lang = _lang(db_user or await get_user(call.from_user.id))
    if await has_pending_order(call.from_user.id):
        await call.answer(t("order_blocked", lang), show_alert=True)
        try:
            await call.message.edit_text(await get_text("order_blocked", lang),
                                         reply_markup=main_menu(lang))
        except Exception:
            pass
        return
    text = t("order_choose_category", lang)
    try:
        await call.message.edit_text(text, reply_markup=choose_category(lang))
    except Exception:
        await call.message.answer(text, reply_markup=choose_category(lang))
    await call.answer()


@router.callback_query(F.data.startswith("order:start:"))
async def order_start(call: CallbackQuery, state: FSMContext, db_user=None):
    key = call.data.split(":")[2]
    if key not in CATALOG:
        await call.answer()
        return
    lang = _lang(db_user or await get_user(call.from_user.id))
    if await has_pending_order(call.from_user.id):
        await call.answer(t("order_blocked", lang), show_alert=True)
        return

    await state.update_data(category=key, lang=lang, attachments=[])
    await state.set_state(OrderForm.task)
    text = (f"<b>{category_title(key, lang)}</b>\n\n" +
            await get_text("order_ask_task", lang))
    try:
        await call.message.edit_text(text, reply_markup=order_cancel(lang))
    except Exception:
        await call.message.answer(text, reply_markup=order_cancel(lang))
    await call.answer()


# ---------- Шаг 1: задача ----------

@router.message(OrderForm.task, F.text)
async def order_task(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer(t("validation_short", lang))
        return
    if len(text) > MAX_TASK_LEN:
        await message.answer(t("validation_long", lang))
        return
    await state.update_data(task=text)
    await state.set_state(OrderForm.deadline)
    await message.answer(await get_text("order_ask_deadline", lang),
                         reply_markup=order_cancel(lang))


@router.message(OrderForm.task)
async def order_task_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(t("send_text", data.get("lang", "ru")))


# ---------- Шаг 2: срок ----------

@router.message(OrderForm.deadline, F.text)
async def order_deadline(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    deadline = (message.text or "").strip()
    if len(deadline) < 2:
        await message.answer(t("validation_short", lang))
        return
    if len(deadline) > MAX_DEADLINE_LEN:
        await message.answer(t("validation_long", lang))
        return
    await state.update_data(deadline=deadline)
    await state.set_state(OrderForm.attach)
    await message.answer(await get_text("order_ask_files", lang),
                         reply_markup=attach_kb(lang, has_files=False))


@router.message(OrderForm.deadline)
async def order_deadline_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(t("send_text", data.get("lang", "ru")))


# ---------- Шаг 3: вложения ----------

def _extract_file(message: Message) -> tuple[str, str, str | None] | None:
    """Возвращает (file_id, file_type, file_name) или None."""
    if message.document:
        return message.document.file_id, "document", message.document.file_name
    if message.photo:
        return message.photo[-1].file_id, "photo", None
    if message.video:
        return message.video.file_id, "video", message.video.file_name
    if message.audio:
        return message.audio.file_id, "audio", message.audio.file_name
    if message.voice:
        return message.voice.file_id, "voice", None
    return None


@router.message(OrderForm.attach)
async def order_attach(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    attachments = data.get("attachments", [])

    extracted = _extract_file(message)
    if not extracted:
        # Текст в режиме приёма файлов — подсказка
        if message.text and not message.text.startswith("/"):
            await message.answer(
                "📎 " + ("Прикрепите файлы или нажмите «Готово»."
                        if lang == "ru" else "Attach files or press «Done».")
            )
        return

    if len(attachments) >= MAX_ATTACHMENTS:
        await message.answer(t("files_too_many", lang).format(n=MAX_ATTACHMENTS))
        return

    file_id, file_type, file_name = extracted
    attachments.append({"file_id": file_id, "file_type": file_type, "file_name": file_name})
    await state.update_data(attachments=attachments)
    await message.answer(
        t("files_added", lang).format(n=len(attachments)),
        reply_markup=attach_kb(lang, has_files=True),
    )


@router.callback_query(F.data == "order:attach_done", OrderForm.attach)
async def attach_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    attachments = data.get("attachments", [])
    repeat = await count_completed_orders(call.from_user.id)

    files_str = (f"{len(attachments)} шт." if lang == "ru" else f"{len(attachments)} pcs.") \
        if attachments else ("нет" if lang == "ru" else "none")

    preview = (await get_text("preview", lang)).format(
        cat=category_title(data["category"], lang),
        task=data["task"],
        deadline=data["deadline"],
        files=files_str,
    )
    if repeat > 0:
        from config import REPEAT_DISCOUNT
        preview += t("preview_discount", lang).format(p=REPEAT_DISCOUNT)
    preview += t("preview_tail", lang)

    await state.set_state(OrderForm.confirm)
    try:
        await call.message.edit_text(preview, reply_markup=order_confirm(lang))
    except Exception:
        await call.message.answer(preview, reply_markup=order_confirm(lang))
    await call.answer()


# ---------- Отмена ----------

@router.callback_query(F.data == "order:cancel")
async def order_cancel_cb(call: CallbackQuery, state: FSMContext, db_user=None):
    data = await state.get_data()
    lang = data.get("lang") or _lang(db_user or await get_user(call.from_user.id))
    await state.clear()
    try:
        await call.message.edit_text(t("order_cancelled", lang),
                                     reply_markup=main_menu(lang))
    except Exception:
        await call.message.answer(t("order_cancelled", lang),
                                  reply_markup=main_menu(lang))
    await call.answer()


# ---------- Подтверждение ----------

@router.callback_query(F.data == "order:confirm", OrderForm.confirm)
async def order_confirm_cb(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    user = call.from_user

    if await has_pending_order(user.id):
        await state.clear()
        await call.message.edit_text(await get_text("order_blocked", lang),
                                     reply_markup=main_menu(lang))
        await call.answer()
        return

    order_id = await create_order(
        user_id=user.id,
        category=category_title(data["category"], "ru"),  # храним в RU для админа
        task=data["task"],
        deadline=data["deadline"],
    )
    # Сохраняем вложения
    for att in data.get("attachments", []):
        await add_attachment(order_id, att["file_id"], att["file_type"], att.get("file_name"))

    attachments = data.get("attachments", [])
    await state.clear()

    # Ответ клиенту
    try:
        await call.message.edit_text(t("order_sent", lang).format(id=order_id),
                                     reply_markup=main_menu(lang))
    except Exception:
        await call.message.answer(t("order_sent", lang).format(id=order_id),
                                  reply_markup=main_menu(lang))
    await call.answer()

    # ----- Уведомление админу -----
    repeat = await count_completed_orders(user.id)
    user_link = (f"@{user.username}" if user.username
                 else f'<a href="tg://user?id={user.id}">{user.full_name}</a>')

    card = (
        f"🔔 <b>Новая заявка №{order_id}</b>\n\n"
        f"<b>Категория:</b> {category_title(data['category'], 'ru')}\n"
        f"<b>Задача:</b>\n<blockquote>{data['task']}</blockquote>\n"
        f"<b>Срок:</b> {data['deadline']}\n"
        f"<b>Вложений:</b> {len(attachments)}\n"
        f"{'🔁 Повторное обращение (' + str(repeat) + ' завершённых)' if repeat else ''}\n\n"
        f"👤 Клиент: {user_link}\n"
        f"🌐 Язык: {lang.upper()}\n"
        f"🆔 <code>{user.id}</code>"
    )

    try:
        await bot.send_message(ADMIN_ID, card, reply_markup=admin_order_actions(order_id))
        # Пересылаем файлы (через copy — без светимости отправителя)
        for att in attachments:
            try:
                if att["file_type"] == "document":
                    await bot.send_document(ADMIN_ID, att["file_id"],
                                            caption=f"📎 К заявке №{order_id}")
                elif att["file_type"] == "photo":
                    await bot.send_photo(ADMIN_ID, att["file_id"],
                                         caption=f"📎 К заявке №{order_id}")
                elif att["file_type"] == "video":
                    await bot.send_video(ADMIN_ID, att["file_id"],
                                         caption=f"📎 К заявке №{order_id}")
                elif att["file_type"] == "audio":
                    await bot.send_audio(ADMIN_ID, att["file_id"],
                                         caption=f"📎 К заявке №{order_id}")
                elif att["file_type"] == "voice":
                    await bot.send_voice(ADMIN_ID, att["file_id"],
                                         caption=f"📎 К заявке №{order_id}")
            except Exception:
                pass
    except Exception:
        pass

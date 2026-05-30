# Анонимная переписка пользователь ↔ админ через бота.
# Пользователь нажимает "Написать в поддержку" → одно сообщение → админу.
# Админ нажимает "Ответить через бота" под заявкой → его сообщения
# копируются клиенту через бота, без раскрытия профиля.
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import get_user, get_order
from utils.i18n import t
from keyboards.inline import support_cancel, main_menu, admin_order_actions
from keyboards.admin import reply_cancel
from states.order import SupportForm
from states.admin import AdminReply

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


# ---------- Поддержка для клиента ----------

@router.callback_query(F.data == "support:start")
async def support_start(call: CallbackQuery, state: FSMContext, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await state.set_state(SupportForm.waiting)
    try:
        await call.message.edit_text(t("support_prompt", lang),
                                     reply_markup=support_cancel(lang))
    except Exception:
        await call.message.answer(t("support_prompt", lang),
                                  reply_markup=support_cancel(lang))
    await call.answer()


@router.callback_query(F.data == "support:cancel", SupportForm.waiting)
async def support_cancel_cb(call: CallbackQuery, state: FSMContext, db_user=None):
    lang = _lang(db_user or await get_user(call.from_user.id))
    await state.clear()
    try:
        await call.message.edit_text(t("main_menu_header", lang),
                                     reply_markup=main_menu(lang))
    except Exception:
        await call.message.answer(t("main_menu_header", lang),
                                  reply_markup=main_menu(lang))
    await call.answer()


@router.message(SupportForm.waiting)
async def support_relay_to_admin(message: Message, state: FSMContext, bot: Bot):
    """Отправляем сообщение клиента админу — карточкой + копией."""
    user = message.from_user
    lang = "ru"
    db_user = await get_user(user.id)
    if db_user:
        lang = db_user.get("language") or "ru"

    await state.clear()

    user_link = (f"@{user.username}" if user.username
                 else f'<a href="tg://user?id={user.id}">{user.full_name}</a>')
    header = (
        "✉️ <b>Сообщение в поддержку</b>\n\n"
        f"От: {user_link}\n"
        f"🌐 {lang.upper()}   🆔 <code>{user.id}</code>\n\n"
        f"<i>Чтобы ответить — используй /reply {user.id} и далее сообщения.</i>"
    )
    try:
        await bot.send_message(ADMIN_ID, header)
        # Копируем оригинал — текст, файл, фото — любой тип
        await bot.copy_message(ADMIN_ID, message.chat.id, message.message_id)
    except Exception:
        pass

    await message.answer(t("support_sent", lang), reply_markup=main_menu(lang))


# ---------- Ответ админа клиенту ----------

@router.callback_query(F.data.startswith("adm:reply:"))
async def admin_start_reply(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Нет прав", show_alert=True)
        return
    order_id = int(call.data.split(":")[2])
    order = await get_order(order_id)
    if not order:
        await call.answer("Заявка не найдена", show_alert=True)
        return
    await state.set_state(AdminReply.waiting)
    await state.update_data(target_user_id=order["user_id"], order_id=order_id)
    await call.message.answer(
        f"💬 <b>Режим ответа клиенту по заявке №{order_id}</b>\n\n"
        "Все ваши сообщения (текст, файлы, фото) будут анонимно "
        "пересланы клиенту через бота.\n\n"
        "<i>Чтобы выйти — нажмите кнопку ниже или отправьте /stop.</i>",
        reply_markup=reply_cancel(order_id),
    )
    await call.answer()


@router.message(Command("reply"))
async def cmd_reply(message: Message, state: FSMContext):
    """/reply <user_id> — начать ответ конкретному пользователю."""
    if message.from_user.id != ADMIN_ID:
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        await message.answer("Использование: <code>/reply &lt;user_id&gt;</code>")
        return
    target = int(parts[1].strip())
    await state.set_state(AdminReply.waiting)
    await state.update_data(target_user_id=target, order_id=None)
    await message.answer(
        f"💬 Режим ответа клиенту <code>{target}</code>. "
        "Отправьте сообщение. /stop — выйти."
    )


@router.message(Command("stop"))
async def cmd_stop(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    cur = await state.get_state()
    if cur == AdminReply.waiting.state:
        await state.clear()
        await message.answer("🛑 Режим ответа завершён.")


@router.callback_query(F.data.startswith("adm:reply_stop:"))
async def admin_stop_reply(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer()
        return
    await state.clear()
    await call.message.edit_text("🛑 Режим ответа завершён.")
    await call.answer()


@router.message(AdminReply.waiting)
async def admin_reply_relay(message: Message, state: FSMContext, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    target = data.get("target_user_id")
    order_id = data.get("order_id")
    if not target:
        return

    # Получатель: язык
    db_user = await get_user(target)
    lang = (db_user and db_user.get("language")) or "ru"

    # Шапка
    intro = t("support_reply_intro", lang)
    if order_id:
        intro += f" <i>({'заявка' if lang == 'ru' else 'request'} №{order_id})</i>"

    try:
        await bot.send_message(target, intro)
        await bot.copy_message(target, message.chat.id, message.message_id)
        await message.reply("✅ Доставлено")
    except Exception as e:
        await message.reply(f"⚠️ Не удалось отправить: {e}")

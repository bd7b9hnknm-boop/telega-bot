# Админ-панель: /panel — текстовый редактор, приветственное фото, ЧС.
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import (
    get_setting, set_setting,
    list_blocked, unblock_user, get_stats,
    STATUS_LABELS,
)
from keyboards.admin import (
    panel_root, texts_menu, text_lang_choice, cancel_edit,
    photo_menu, blocked_list_kb, EDITABLE_TEXTS,
)
from states.admin import AdminEdit
from utils.i18n import t

router = Router()


def _is_admin(uid: int) -> bool:
    return uid == ADMIN_ID


# ---------- Точка входа ----------

@router.message(Command("panel", "admin"))
async def open_panel(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "<b>🛠 Панель администратора</b>\n\n"
        "▸ Редактирование текстов и приветственного фото\n"
        "▸ Управление чёрным списком\n"
        "▸ Статистика\n\n"
        "<i>Также доступно: /stats, /reply &lt;user_id&gt;</i>",
        reply_markup=panel_root(),
    )


@router.callback_query(F.data == "pnl:home")
async def panel_home(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    await state.clear()
    try:
        await call.message.edit_text(
            "<b>🛠 Панель администратора</b>",
            reply_markup=panel_root(),
        )
    except Exception:
        await call.message.answer("<b>🛠 Панель администратора</b>",
                                  reply_markup=panel_root())
    await call.answer()


@router.callback_query(F.data == "pnl:close")
async def panel_close(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    await state.clear()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.answer("Закрыто")


# ---------- Статистика ----------

@router.callback_query(F.data == "pnl:stats")
async def panel_stats(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    s = await get_stats()
    text = (
        "<b>📊 Статистика</b>\n\n"
        f"👥 Пользователей: <b>{s['users']}</b>\n"
        f"🚫 В ЧС: <b>{s['blocked']}</b>\n"
        f"📦 Всего заявок: <b>{s['total']}</b>\n\n"
        f"🟡 На рассмотрении: <b>{s['pending']}</b>\n"
        f"🟢 В работе: <b>{s['accepted']}</b>\n"
        f"✅ Выполнены: <b>{s['completed']}</b>\n"
        f"🔴 Отклонены: <b>{s['rejected']}</b>"
    )
    await call.message.edit_text(text, reply_markup=panel_root())
    await call.answer()


# ---------- Редактирование текстов ----------

@router.callback_query(F.data == "pnl:texts")
async def panel_texts(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    await call.message.edit_text(
        "<b>📝 Редактор текстов</b>\n\n"
        "Выберите фрагмент, который нужно изменить.",
        reply_markup=texts_menu(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("pnl:txt:"))
async def panel_text_choose_lang(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    key = call.data.split(":", 2)[2]
    label = dict(EDITABLE_TEXTS).get(key, key)

    # Показываем текущие значения для обоих языков
    ru_cur = await get_setting(f"text:ru:{key}") or t(key, "ru")
    en_cur = await get_setting(f"text:en:{key}") or t(key, "en")

    def _short(s: str) -> str:
        s = s.replace("\n", " ")
        return s[:200] + ("…" if len(s) > 200 else "")

    text = (
        f"<b>{label}</b>\n\n"
        f"<b>🇷🇺 RU:</b> <i>{_short(ru_cur)}</i>\n\n"
        f"<b>🇬🇧 EN:</b> <i>{_short(en_cur)}</i>\n\n"
        "Выберите язык для редактирования или сбросьте к стандарту."
    )
    await call.message.edit_text(text, reply_markup=text_lang_choice(key))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:edit:"))
async def panel_text_edit(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    _, _, key, lang = call.data.split(":")
    await state.set_state(AdminEdit.waiting_text)
    await state.update_data(edit_key=key, edit_lang=lang)
    label = dict(EDITABLE_TEXTS).get(key, key)
    await call.message.edit_text(
        f"✏️ <b>Новый текст для «{label}» ({lang.upper()})</b>\n\n"
        "Отправьте новый текст следующим сообщением.\n"
        "Поддерживается HTML: <code>&lt;b&gt;</code>, <code>&lt;i&gt;</code>, "
        "<code>&lt;blockquote&gt;</code>, переводы строк.\n\n"
        "<i>В тексте приветствия используйте {name} для подстановки имени.</i>",
        reply_markup=cancel_edit(),
    )
    await call.answer()


@router.message(AdminEdit.waiting_text, F.text)
async def panel_text_save(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    data = await state.get_data()
    key = data.get("edit_key")
    lang = data.get("edit_lang")
    if not key or not lang:
        await state.clear()
        return
    await set_setting(f"text:{lang}:{key}", message.html_text)
    await state.clear()
    await message.answer(
        f"✅ Текст «{key}» ({lang.upper()}) обновлён.",
        reply_markup=panel_root(),
    )


@router.message(AdminEdit.waiting_text)
async def panel_text_save_invalid(message: Message):
    await message.answer("⚠️ Пришлите текстовое сообщение.")


@router.callback_query(F.data.startswith("pnl:reset:"))
async def panel_text_reset(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    key = call.data.split(":", 2)[2]
    await set_setting(f"text:ru:{key}", None)
    await set_setting(f"text:en:{key}", None)
    await call.answer("Сброшено к стандарту", show_alert=True)
    # Возвращаемся к списку
    await call.message.edit_text(
        "<b>📝 Редактор текстов</b>\n\nВыберите фрагмент.",
        reply_markup=texts_menu(),
    )


# ---------- Приветственное фото ----------

@router.callback_query(F.data == "pnl:photo")
async def panel_photo(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    photo_id = await get_setting("welcome_photo")
    text = (
        "<b>🖼 Приветственное фото</b>\n\n"
        + ("✅ Сейчас установлено." if photo_id else "❌ Не установлено.")
        + "\n\nОно показывается над приветствием при /start."
    )
    await call.message.edit_text(text, reply_markup=photo_menu(bool(photo_id)))
    await call.answer()


@router.callback_query(F.data == "pnl:photo_set")
async def panel_photo_set(call: CallbackQuery, state: FSMContext):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    await state.set_state(AdminEdit.waiting_photo)
    await call.message.edit_text(
        "📤 Отправьте фотографию следующим сообщением.\n\n"
        "<i>Можно также отправить смайл/эмодзи — он будет добавлен в приветствие.</i>",
        reply_markup=cancel_edit(),
    )
    await call.answer()


@router.message(AdminEdit.waiting_photo, F.photo)
async def panel_photo_save(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    photo_id = message.photo[-1].file_id
    await set_setting("welcome_photo", photo_id)
    await state.clear()
    await message.answer("✅ Приветственное фото обновлено.", reply_markup=panel_root())


@router.message(AdminEdit.waiting_photo)
async def panel_photo_invalid(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("⚠️ Нужна именно фотография.")


@router.callback_query(F.data == "pnl:photo_del")
async def panel_photo_del(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    await set_setting("welcome_photo", None)
    await call.answer("Удалено", show_alert=True)
    await call.message.edit_text(
        "<b>🖼 Приветственное фото</b>\n\n❌ Не установлено.",
        reply_markup=photo_menu(False),
    )


# ---------- Чёрный список ----------

@router.callback_query(F.data == "pnl:blocked")
async def panel_blocked(call: CallbackQuery):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    users = await list_blocked(limit=30)
    if not users:
        await call.message.edit_text(
            "<b>🚫 Чёрный список</b>\n\n<i>Пусто.</i>",
            reply_markup=panel_root(),
        )
    else:
        lines = ["<b>🚫 Чёрный список</b>", ""]
        for u in users:
            uname = f"@{u['username']}" if u["username"] else (u["full_name"] or "—")
            reason = u.get("block_reason") or "—"
            lines.append(f"▸ <code>{u['id']}</code> {uname}  ·  {reason}")
        await call.message.edit_text("\n".join(lines),
                                     reply_markup=blocked_list_kb(users))
    await call.answer()


@router.callback_query(F.data.startswith("pnl:unblock:"))
async def panel_unblock(call: CallbackQuery, bot: Bot):
    if not _is_admin(call.from_user.id):
        await call.answer()
        return
    user_id = int(call.data.split(":")[2])
    await unblock_user(user_id)

    # Уведомляем пользователя
    try:
        await bot.send_message(
            user_id,
            "✅ Доступ к боту восстановлен. Отправьте /start, чтобы начать."
        )
    except Exception:
        pass

    await call.answer("Разблокирован", show_alert=True)
    # Обновляем список
    users = await list_blocked(limit=30)
    if not users:
        await call.message.edit_text(
            "<b>🚫 Чёрный список</b>\n\n<i>Пусто.</i>",
            reply_markup=panel_root(),
        )
    else:
        lines = ["<b>🚫 Чёрный список</b>", ""]
        for u in users:
            uname = f"@{u['username']}" if u["username"] else (u["full_name"] or "—")
            reason = u.get("block_reason") or "—"
            lines.append(f"▸ <code>{u['id']}</code> {uname}  ·  {reason}")
        await call.message.edit_text("\n".join(lines),
                                     reply_markup=blocked_list_kb(users))

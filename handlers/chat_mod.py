# Модерация группового чата. Команды доступны только админу бота.
# Команды (reply на сообщение нарушителя):
#   /mute [мин]   — замутить (по умолчанию 60 мин)
#   /unmute       — снять мут
#   /ban          — забанить
#   /unban <id>   — разбан
#   /warn [текст] — предупредить (логируется)
#   /del          — удалить сообщение
# Команды без reply работают по @username или id в первом аргументе.
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, ChatPermissions
import aiosqlite

from config import ADMIN_ID, DB_PATH

router = Router()


def _is_admin(uid) -> bool:
    return uid == ADMIN_ID


async def _log(chat_id, target_id, action, by, duration=None, reason=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO chat_mod (chat_id, target_user_id, action, duration_min,
                                  reason, by_admin, created_at)
            VALUES (?,?,?,?,?,?,?)
        """, (chat_id, target_id, action, duration, reason, by,
              datetime.utcnow().isoformat()))
        await db.commit()


def _target_from_message(message: Message) -> tuple[int | None, str | None]:
    """Берём цель из reply или из аргумента команды."""
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, (u.username or u.full_name)
    parts = (message.text or "").split()
    if len(parts) >= 2:
        arg = parts[1].lstrip("@")
        if arg.isdigit():
            return int(arg), arg
    return None, None


@router.message(Command("mute"))
async def cmd_mute(message: Message, bot: Bot):
    if not _is_admin(message.from_user.id) or message.chat.type == "private":
        return
    target_id, name = _target_from_message(message)
    if not target_id:
        await message.reply("Использование: /mute (reply) [минут]"); return
    parts = (message.text or "").split()
    minutes = 60
    for p in parts[1:]:
        if p.isdigit():
            minutes = int(p); break
    until = datetime.utcnow() + timedelta(minutes=minutes)
    perms = ChatPermissions(can_send_messages=False)
    try:
        await bot.restrict_chat_member(message.chat.id, target_id, permissions=perms,
                                       until_date=until)
        await _log(message.chat.id, target_id, "mute", message.from_user.id,
                   duration=minutes)
        await message.reply(f"🔇 Замучен на {minutes} мин.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, bot: Bot):
    if not _is_admin(message.from_user.id) or message.chat.type == "private":
        return
    target_id, _ = _target_from_message(message)
    if not target_id:
        await message.reply("Использование: /unmute (reply / id)"); return
    perms = ChatPermissions(
        can_send_messages=True, can_send_audios=True, can_send_documents=True,
        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
        can_send_voice_notes=True, can_send_polls=True,
        can_send_other_messages=True, can_add_web_page_previews=True,
    )
    try:
        await bot.restrict_chat_member(message.chat.id, target_id, permissions=perms)
        await _log(message.chat.id, target_id, "unmute", message.from_user.id)
        await message.reply("🔊 Размучен.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")


@router.message(Command("ban"))
async def cmd_ban(message: Message, bot: Bot):
    if not _is_admin(message.from_user.id) or message.chat.type == "private":
        return
    target_id, _ = _target_from_message(message)
    if not target_id:
        await message.reply("Использование: /ban (reply / id)"); return
    try:
        await bot.ban_chat_member(message.chat.id, target_id)
        await _log(message.chat.id, target_id, "ban", message.from_user.id)
        await message.reply("🚫 Забанен.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")


@router.message(Command("unban"))
async def cmd_unban(message: Message, bot: Bot):
    if not _is_admin(message.from_user.id) or message.chat.type == "private":
        return
    target_id, _ = _target_from_message(message)
    if not target_id:
        await message.reply("Использование: /unban (id)"); return
    try:
        await bot.unban_chat_member(message.chat.id, target_id)
        await _log(message.chat.id, target_id, "unban", message.from_user.id)
        await message.reply("✅ Разбан.")
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")


@router.message(Command("warn"))
async def cmd_warn(message: Message):
    if not _is_admin(message.from_user.id) or message.chat.type == "private":
        return
    target_id, name = _target_from_message(message)
    if not target_id:
        await message.reply("Использование: /warn (reply) [причина]"); return
    parts = (message.text or "").split(maxsplit=1)
    reason = parts[1] if len(parts) > 1 else "Нарушение правил"
    await _log(message.chat.id, target_id, "warn", message.from_user.id,
               reason=reason)
    await message.reply(f"⚠️ <b>Предупреждение</b> для {name or target_id}\n{reason}")


@router.message(Command("del"))
async def cmd_del(message: Message, bot: Bot):
    if not _is_admin(message.from_user.id) or message.chat.type == "private":
        return
    if not message.reply_to_message:
        await message.reply("Используется реплаем на сообщение."); return
    try:
        await bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        await message.delete()
        await _log(message.chat.id, message.reply_to_message.from_user.id,
                   "delete", message.from_user.id)
    except Exception as e:
        await message.reply(f"⚠️ Ошибка: {e}")

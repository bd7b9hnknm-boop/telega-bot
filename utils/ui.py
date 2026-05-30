# Утилиты для аккуратного UI: редактирование сообщений с фолбэком на send,
# проверка длины, безопасные обрезки.
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest


MAX_LEN = 3900   # запас от лимита 4096


def cut(text: str) -> str:
    """Обрезать длинное сообщение с пометкой о сокращении."""
    if len(text) <= MAX_LEN:
        return text
    return text[:MAX_LEN] + "\n\n<i>…сокращено</i>"


async def edit_or_send(call: CallbackQuery, text: str,
                       reply_markup: InlineKeyboardMarkup | None = None) -> None:
    """Универсальное обновление сообщения в callback-хендлере.

    Кейсы:
    1. Текстовое сообщение → edit_text
    2. Сообщение с фото → нельзя edit_text, удаляем + отправляем заново
    3. «Не изменилось» (тот же текст и kb) → молча игнорируем
    4. Любая другая ошибка → fallback на answer (новое сообщение)
    """
    text = cut(text)
    msg = call.message
    try:
        if msg.photo or msg.video or msg.document or msg.animation:
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer(text, reply_markup=reply_markup)
            return
        await msg.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        # «message is not modified» — нормально, просто игнор
        if "not modified" in str(e):
            return
        try:
            await msg.answer(text, reply_markup=reply_markup)
        except Exception:
            pass
    except Exception:
        try:
            await msg.answer(text, reply_markup=reply_markup)
        except Exception:
            pass

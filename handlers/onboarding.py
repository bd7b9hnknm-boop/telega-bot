# Онбординг: выбор языка → выбор причины → главное меню (или блок).
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_user, set_user_field, block_user, get_setting
from keyboards.inline import language_kb, purpose_kb, main_menu
from utils.i18n import t, get_text

router = Router()


async def _show_welcome(message_or_call, lang: str, name: str) -> None:
    """Приветствие с опциональным фото из настроек."""
    photo_id = await get_setting("welcome_photo")
    text = (await get_text("welcome", lang)).format(name=name)
    kb = main_menu(lang)

    target = message_or_call if isinstance(message_or_call, Message) else message_or_call.message
    bot = target.bot
    chat_id = target.chat.id

    if photo_id:
        try:
            await bot.send_photo(chat_id, photo_id, caption=text, reply_markup=kb)
            return
        except Exception:
            pass
    await bot.send_message(chat_id, text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user(message.from_user.id)
    # Новый — спрашиваем язык
    if not user or not user.get("language"):
        await message.answer(t("choose_language"), reply_markup=language_kb())
        return
    lang = user["language"]
    # Язык есть, но не выбрана причина — спрашиваем
    if not user.get("purpose"):
        await message.answer(t("choose_purpose", lang), reply_markup=purpose_kb(lang))
        return
    # Всё ок — главное меню
    await _show_welcome(message, lang, message.from_user.first_name)


# ---------- Выбор языка ----------

@router.callback_query(F.data.startswith("lang:"))
async def choose_language(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":", 1)[1]
    if lang not in ("ru", "en"):
        await call.answer()
        return
    await set_user_field(call.from_user.id, "language", lang)
    user = await get_user(call.from_user.id)

    # Если причина уже выбрана — показываем меню сразу
    if user and user.get("purpose"):
        try:
            await call.message.delete()
        except Exception:
            pass
        await _show_welcome(call, lang, call.from_user.first_name)
    else:
        try:
            await call.message.edit_text(t("choose_purpose", lang),
                                         reply_markup=purpose_kb(lang))
        except Exception:
            await call.message.answer(t("choose_purpose", lang),
                                      reply_markup=purpose_kb(lang))
    await call.answer()


# ---------- Смена языка из меню ----------

@router.callback_query(F.data == "nav:lang")
async def nav_lang(call: CallbackQuery):
    await call.message.edit_text(t("choose_language"), reply_markup=language_kb())
    await call.answer()


# ---------- Выбор причины ----------

@router.callback_query(F.data == "purpose:ttzht")
async def purpose_ttzht(call: CallbackQuery, state: FSMContext):
    user = await get_user(call.from_user.id)
    lang = (user and user.get("language")) or "ru"
    await set_user_field(call.from_user.id, "purpose", "ttzht")
    try:
        await call.message.delete()
    except Exception:
        pass
    await _show_welcome(call, lang, call.from_user.first_name)
    await call.answer()


@router.callback_query(F.data == "purpose:other")
async def purpose_other(call: CallbackQuery):
    user = await get_user(call.from_user.id)
    lang = (user and user.get("language")) or "ru"
    # Блокируем
    await block_user(call.from_user.id, "purpose:other")
    try:
        await call.message.edit_text(t("blocked", lang))
    except Exception:
        await call.message.answer(t("blocked", lang))
    await call.answer()

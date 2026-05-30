# Обработчик оформления заявки — простой пошаговый диалог
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from handlers.start import main_menu

router = Router()


class OrderForm(StatesGroup):
    """Состояния диалога оформления заявки."""
    task = State()      # что нужно сделать
    deadline = State()  # срок


@router.message(F.text == "📩 Заказать")
async def order_start(message: Message, state: FSMContext):
    """Начало оформления заявки."""
    await state.set_state(OrderForm.task)
    await message.answer(
        "📝 Опиши, что нужно сделать (тема, требования, объём):",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(OrderForm.task)
async def order_task(message: Message, state: FSMContext):
    """Принимаем описание задачи и спрашиваем срок."""
    await state.update_data(task=message.text)
    await state.set_state(OrderForm.deadline)
    await message.answer("⏰ К какому сроку нужно сделать?")


@router.message(OrderForm.deadline)
async def order_deadline(message: Message, state: FSMContext, bot: Bot):
    """Принимаем срок и отправляем заявку администратору."""
    await state.update_data(deadline=message.text)
    data = await state.get_data()
    await state.clear()

    user = message.from_user
    # Контакт: юзернейм если есть, иначе ссылка по ID
    if user.username:
        contact = f"@{user.username}"
    else:
        contact = f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

    # Заявка для админа
    admin_text = (
        "🔔 <b>Новая заявка!</b>\n\n"
        f"👤 От: {contact} (ID: <code>{user.id}</code>)\n\n"
        f"📝 <b>Что нужно:</b>\n{data.get('task')}\n\n"
        f"⏰ <b>Срок:</b> {data.get('deadline')}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text)
        reply = (
            "✅ Заявка отправлена!\n\n"
            "В ближайшее время с тобой свяжутся для подтверждения "
            "и отправки реквизитов оплаты."
        )
    except Exception:
        reply = (
            "⚠️ Не удалось отправить заявку автоматически.\n"
            "Напиши администратору напрямую."
        )

    await message.answer(reply, reply_markup=main_menu())

# Оформление заявки через FSM с подтверждением и антиспамом
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from database import (
    has_pending_order,
    create_order,
    count_completed_orders,
    upsert_user,
)
from utils.catalog import CATALOG, category_title
from utils.texts import (
    ORDER_BLOCKED,
    ORDER_ASK_TASK,
    ORDER_ASK_DEADLINE,
    ORDER_CANCELLED,
    order_preview,
    order_sent,
    admin_new_order,
)
from keyboards.inline import (
    choose_category,
    order_cancel,
    order_confirm,
    main_menu,
    admin_order_actions,
)
from states.order import OrderForm

# Максимальная длина пользовательского ввода (защита от мусора)
MAX_TASK_LEN = 1500
MAX_DEADLINE_LEN = 100

router = Router()


# ---------- Запуск оформления ----------

@router.callback_query(F.data == "order:choose")
async def order_choose(call: CallbackQuery, state: FSMContext):
    """Спросить категорию перед началом FSM."""
    await state.clear()
    if await has_pending_order(call.from_user.id):
        await call.answer("У вас уже есть активная заявка", show_alert=True)
        await call.message.edit_text(ORDER_BLOCKED, reply_markup=main_menu())
        return
    await call.message.edit_text(
        "<b>📩 Новая заявка</b>\n\n<i>Выберите категорию услуги:</i>",
        reply_markup=choose_category(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("order:start:"))
async def order_start(call: CallbackQuery, state: FSMContext):
    """Старт FSM с выбранной категорией."""
    key = call.data.split(":")[2]
    if key not in CATALOG:
        await call.answer("Категория не найдена", show_alert=True)
        return
    if await has_pending_order(call.from_user.id):
        await call.answer("У вас уже есть активная заявка", show_alert=True)
        await call.message.edit_text(ORDER_BLOCKED, reply_markup=main_menu())
        return

    await state.update_data(category=key)
    await state.set_state(OrderForm.task)
    await call.message.edit_text(
        f"<b>Категория:</b> {category_title(key)}\n\n{ORDER_ASK_TASK}",
        reply_markup=order_cancel(),
    )
    await call.answer()


# ---------- Шаги ввода ----------

@router.message(OrderForm.task, F.text)
async def order_task(message: Message, state: FSMContext):
    """Принимаем описание задачи."""
    text = (message.text or "").strip()
    if len(text) < 5:
        await message.answer("⚠️ Описание слишком короткое. Опишите подробнее.")
        return
    if len(text) > MAX_TASK_LEN:
        await message.answer(
            f"⚠️ Описание слишком длинное (макс. {MAX_TASK_LEN} символов). Сократите."
        )
        return
    await state.update_data(task=text)
    await state.set_state(OrderForm.deadline)
    await message.answer(ORDER_ASK_DEADLINE, reply_markup=order_cancel())


@router.message(OrderForm.task)
async def order_task_invalid(message: Message):
    await message.answer("⚠️ Отправьте описание задачи текстом.")


@router.message(OrderForm.deadline, F.text)
async def order_deadline(message: Message, state: FSMContext):
    """Принимаем срок и показываем превью."""
    deadline = (message.text or "").strip()
    if len(deadline) < 2:
        await message.answer("⚠️ Укажите срок чуть подробнее.")
        return
    if len(deadline) > MAX_DEADLINE_LEN:
        await message.answer("⚠️ Слишком длинный текст для срока.")
        return

    await state.update_data(deadline=deadline)
    data = await state.get_data()
    repeat = await count_completed_orders(message.from_user.id)

    await state.set_state(OrderForm.confirm)
    await message.answer(
        order_preview(
            category_title(data["category"]),
            data["task"],
            deadline,
            discount=repeat > 0,
        ),
        reply_markup=order_confirm(),
    )


@router.message(OrderForm.deadline)
async def order_deadline_invalid(message: Message):
    await message.answer("⚠️ Отправьте срок текстом.")


# ---------- Подтверждение / отмена ----------

@router.callback_query(F.data == "order:cancel")
async def order_cancel_cb(call: CallbackQuery, state: FSMContext):
    """Отмена на любом шаге."""
    await state.clear()
    await call.message.edit_text(ORDER_CANCELLED, reply_markup=main_menu())
    await call.answer("Отменено")


@router.callback_query(F.data == "order:confirm", OrderForm.confirm)
async def order_confirm_cb(call: CallbackQuery, state: FSMContext, bot: Bot):
    """Сохранение заявки + уведомление администратора."""
    data = await state.get_data()
    user = call.from_user

    # На всякий случай обновим запись пользователя
    await upsert_user(user.id, user.username, user.full_name)

    # Финальная проверка антиспама (защита от двойного нажатия)
    if await has_pending_order(user.id):
        await state.clear()
        await call.message.edit_text(ORDER_BLOCKED, reply_markup=main_menu())
        await call.answer("Уже есть активная заявка", show_alert=True)
        return

    order_id = await create_order(
        user_id=user.id,
        category=category_title(data["category"]),
        task=data["task"],
        deadline=data["deadline"],
    )
    await state.clear()

    # Уведомление пользователю
    await call.message.edit_text(order_sent(order_id), reply_markup=main_menu())
    await call.answer("Заявка отправлена")

    # Уведомление администратора
    user_link = (
        f"@{user.username}" if user.username
        else f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
    )
    repeat = await count_completed_orders(user.id)
    try:
        await bot.send_message(
            ADMIN_ID,
            admin_new_order(
                order_id=order_id,
                category=category_title(data["category"]),
                task=data["task"],
                deadline=data["deadline"],
                user_link=user_link,
                user_id=user.id,
                repeat=repeat,
            ),
            reply_markup=admin_order_actions(order_id, user.id),
        )
    except Exception:
        # Если админ не запускал бота — игнорируем, заявка уже в БД
        pass

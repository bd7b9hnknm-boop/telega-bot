# Оплата заявок: карта/СБП (реквизиты + ручное подтверждение)
# и крипта через CryptoBot (USDT).
import asyncio
import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery

from config import ADMIN_ID
from database import (
    get_user, get_order, get_setting,
    create_payment, set_payment_status,
    list_pending_payments, get_payment_by_external,
    set_order_status, STATUS_ACCEPTED, STATUS_COMPLETED,
    P_PAID, P_PENDING,
)
from utils.i18n import t, get_text
from keyboards.inline import pay_methods, pay_card_kb, pay_crypto_kb, main_menu
from integrations import cryptobot

router = Router()


def _lang(db_user) -> str:
    return (db_user and db_user.get("language")) or "ru"


# ---------- Выбор способа ----------

@router.callback_query(F.data.startswith("pay:choose:"))
async def pay_choose(call: CallbackQuery, db_user=None):
    order_id = int(call.data.split(":")[2])
    order = await get_order(order_id)
    if not order or order["user_id"] != call.from_user.id:
        await call.answer("Заявка не найдена", show_alert=True); return
    if order["status"] != STATUS_ACCEPTED:
        await call.answer("Заявка ещё не принята к оплате", show_alert=True); return

    lang = _lang(db_user or await get_user(call.from_user.id))
    amount = await get_setting(f"order_amount:{order_id}") or "по договорённости"
    card_req = await get_setting("pay:card_requisites")
    has_card = bool(card_req and card_req.strip())
    has_crypto = cryptobot.is_enabled()

    if not has_card and not has_crypto:
        await call.message.edit_text(
            t("pay_no_methods", lang), reply_markup=main_menu(lang))
        await call.answer(); return

    text = t("pay_choose", lang).format(id=order_id, amount=amount)
    try:
        await call.message.edit_text(text,
            reply_markup=pay_methods(lang, order_id, has_card, has_crypto))
    except Exception:
        await call.message.answer(text,
            reply_markup=pay_methods(lang, order_id, has_card, has_crypto))
    await call.answer()


# ---------- Карта ----------

@router.callback_query(F.data.startswith("pay:card:"))
async def pay_card(call: CallbackQuery, db_user=None):
    order_id = int(call.data.split(":")[2])
    order = await get_order(order_id)
    if not order or order["user_id"] != call.from_user.id:
        await call.answer(); return
    lang = _lang(db_user or await get_user(call.from_user.id))

    req = await get_setting("pay:card_requisites") or "—"
    amount = await get_setting(f"order_amount:{order_id}") or "по договорённости"

    payment_id = await create_payment(
        user_id=call.from_user.id, method="card", amount=amount, order_id=order_id)

    text = t("pay_card", lang).format(req=req, amount=amount)
    try:
        await call.message.edit_text(text, reply_markup=pay_card_kb(lang, payment_id))
    except Exception:
        await call.message.answer(text, reply_markup=pay_card_kb(lang, payment_id))
    await call.answer()


@router.callback_query(F.data.startswith("pay:claim:"))
async def pay_card_claim(call: CallbackQuery, bot: Bot, db_user=None):
    payment_id = int(call.data.split(":")[2])
    lang = _lang(db_user or await get_user(call.from_user.id))

    # Уведомление админу для сверки
    try:
        await bot.send_message(
            ADMIN_ID,
            f"💳 <b>Пользователь отметил оплату по платежу #{payment_id}</b>\n"
            f"От: <a href=\"tg://user?id={call.from_user.id}\">{call.from_user.full_name}</a>\n"
            f"🆔 <code>{call.from_user.id}</code>\n\n"
            f"<i>Сверьте поступление и при необходимости подтвердите вручную.</i>"
        )
    except Exception:
        pass

    await call.message.edit_text(t("pay_card_claimed", lang),
                                 reply_markup=main_menu(lang))
    await call.answer()


# ---------- Крипта ----------

@router.callback_query(F.data.startswith("pay:crypto:"))
async def pay_crypto(call: CallbackQuery, db_user=None):
    order_id = int(call.data.split(":")[2])
    order = await get_order(order_id)
    if not order or order["user_id"] != call.from_user.id:
        await call.answer(); return
    if not cryptobot.is_enabled():
        await call.answer("CryptoBot не настроен", show_alert=True); return

    lang = _lang(db_user or await get_user(call.from_user.id))

    # Сумма в USDT — администратор задаёт через panel:
    # ключ: order_amount_usdt:<id>
    amount_usdt = await get_setting(f"order_amount_usdt:{order_id}")
    if not amount_usdt:
        await call.answer("Сумма в USDT не задана. Свяжитесь с поддержкой.",
                          show_alert=True); return

    try:
        invoice = await cryptobot.create_invoice(
            amount=amount_usdt, asset="USDT",
            description=f"Order #{order_id}",
            payload=f"order:{order_id}",
        )
    except Exception as e:
        logging.exception("CryptoBot invoice error")
        await call.answer(f"Ошибка создания счёта: {e}", show_alert=True); return

    payment_id = await create_payment(
        user_id=call.from_user.id, method="cryptobot",
        amount=amount_usdt, order_id=order_id,
        external_id=str(invoice["invoice_id"]),
    )

    text = t("pay_crypto_invoice", lang).format(amount=amount_usdt)
    url = invoice.get("bot_invoice_url") or invoice.get("mini_app_invoice_url") or invoice.get("web_app_invoice_url")
    try:
        await call.message.edit_text(text,
            reply_markup=pay_crypto_kb(lang, url, payment_id))
    except Exception:
        await call.message.answer(text,
            reply_markup=pay_crypto_kb(lang, url, payment_id))
    await call.answer()


@router.callback_query(F.data.startswith("pay:check:"))
async def pay_check(call: CallbackQuery, bot: Bot, db_user=None):
    await _poll_once(bot)
    await call.answer("Проверено", show_alert=False)


# ---------- Фоновый поллер CryptoBot ----------

async def _poll_once(bot: Bot) -> None:
    """Опрашиваем статусы активных крипто-инвойсов раз за вызов."""
    if not cryptobot.is_enabled():
        return
    pending = await list_pending_payments(method="cryptobot")
    if not pending:
        return
    ids = [int(p["external_id"]) for p in pending if p.get("external_id")]
    if not ids:
        return
    try:
        items = await cryptobot.get_invoices(ids)
    except Exception:
        logging.exception("CryptoBot getInvoices failed")
        return
    for inv in items:
        if inv.get("status") != "paid":
            continue
        ext_id = str(inv["invoice_id"])
        pay = await get_payment_by_external(ext_id)
        if not pay or pay["status"] == P_PAID:
            continue
        await set_payment_status(pay["id"], P_PAID)
        # Уведомление клиенту
        try:
            await bot.send_message(
                pay["user_id"],
                f"✅ <b>Оплата по заявке №{pay['order_id']} получена.</b>\n\n"
                f"Сумма: {pay['amount']} USDT.\n"
                "Работа начата. О готовности сообщим отдельно."
            )
        except Exception:
            pass
        # Уведомление админу
        try:
            await bot.send_message(
                ADMIN_ID,
                f"🪙 <b>Поступила оплата по заявке №{pay['order_id']}</b>\n"
                f"Сумма: {pay['amount']} USDT\n"
                f"От: <code>{pay['user_id']}</code>"
            )
        except Exception:
            pass


async def crypto_polling_task(bot: Bot) -> None:
    while True:
        try:
            await _poll_once(bot)
        except Exception:
            logging.exception("crypto poll error")
        await asyncio.sleep(30)

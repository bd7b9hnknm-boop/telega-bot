# Минимальный клиент Crypto Pay API (@CryptoBot).
# Документация: https://help.crypt.bot/crypto-pay-api
import aiohttp
from typing import Optional

from config import CRYPTOBOT_TOKEN, CRYPTOBOT_TESTNET


BASE_URL = ("https://testnet-pay.crypt.bot/api"
            if CRYPTOBOT_TESTNET else "https://pay.crypt.bot/api")


def is_enabled() -> bool:
    return bool(CRYPTOBOT_TOKEN)


async def _call(method: str, payload: dict | None = None) -> dict:
    if not CRYPTOBOT_TOKEN:
        raise RuntimeError("CRYPTOBOT_TOKEN не задан")
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{BASE_URL}/{method}", json=payload or {},
                          headers=headers, timeout=15) as r:
            data = await r.json()
            if not data.get("ok"):
                raise RuntimeError(f"CryptoBot API error: {data}")
            return data["result"]


async def create_invoice(amount: str, asset: str = "USDT",
                         description: str = "",
                         payload: str = "",
                         hidden_message: str = "") -> dict:
    """Возвращает dict с полями invoice_id, status, bot_invoice_url..."""
    body = {
        "asset": asset,
        "amount": str(amount),
        "description": description[:1024],
        "payload": payload[:4096],
        "hidden_message": hidden_message[:2048],
        "paid_btn_name": "callback",
        "allow_anonymous": True,
    }
    return await _call("createInvoice", body)


async def get_invoices(invoice_ids: list[int]) -> list[dict]:
    body = {"invoice_ids": ",".join(str(i) for i in invoice_ids)}
    res = await _call("getInvoices", body)
    return res.get("items", []) if isinstance(res, dict) else res


async def delete_invoice(invoice_id: int) -> bool:
    try:
        await _call("deleteInvoice", {"invoice_id": invoice_id})
        return True
    except Exception:
        return False

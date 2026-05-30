# Парсер страницы замен ТТЖТ.
# Источник: https://www.ttgdt.stu.ru/students/zam
#
# На странице может быть несколько таблиц (на сегодня, завтра и т.д.).
# Каждая начинается заголовком <h1>Замены на DD месяц YYYY года</h1>.
# Структура таблицы:
#   tr[0]: заголовок колонок
#   tr[N]: Группа | Пара | Заменяемый предмет | Замена | Ауд.
#   - Пустая ячейка группы = продолжение предыдущей
#   - Строки полностью без данных — игнорируем
#   - После списка замен идут «хвостовые» пустые строки и «Заведующая учебным отделом»
import re
import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

from config import SCHEDULE_PROXY

SOURCE_URL = "https://www.ttgdt.stu.ru/students/zam"

# Заголовки HTTP — представляемся обычным браузером
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ru,en;q=0.8",
}


@dataclass
class ReplaceRow:
    groups: list[str]      # ['151'] или ['251', '253']
    pair: str              # '1,2' | '8.00' | '1'
    subject_old: str       # 'Физика' | '-->'
    subject_new: str       # 'Математика' | 'НЕТ'
    room: str              # '206' | ''

    def affects(self, group: str) -> bool:
        return group in self.groups


@dataclass
class ScheduleDay:
    date_text: str         # «30 мая 2026 года»
    rows: list[ReplaceRow]


# ------------------------------------------------------------------

_GROUP_SPLIT = re.compile(r"[\s,.;/]+")


def _fix_excel_float(raw: str) -> str:
    """Исправляет float-баги Excel: '553.5549999999999' → '553.555'."""
    s = raw.strip()
    # Один вход — целиком float-подобное число
    if re.fullmatch(r"\d+\.\d+", s):
        whole, frac = s.split(".")
        if len(frac) > 4:
            try:
                f = float(s)
                # Округляем до 3 знаков (стандарт 3-значных групп)
                rounded = round(f, 3)
                # Печатаем без хвостовых нулей
                s = format(rounded, ".3f").rstrip("0").rstrip(".")
            except ValueError:
                pass
    return s


def _normalize_groups(raw: str) -> list[str]:
    """Распарсить ячейку 'Группа'. Допускаем '151', '251,253', '141, 152',
    '751.753', а также мусор вида '553.5549999999999' (Excel-баг)."""
    if not raw or not raw.strip():
        return []
    cleaned = _fix_excel_float(raw)
    parts = [p.strip() for p in _GROUP_SPLIT.split(cleaned) if p.strip()]
    out = []
    for p in parts:
        # Учитываем формы 151, 551-П, 241-П — оставляем как есть.
        # Отбрасываем явный мусор длиной > 6 цифр (бывший хвост float).
        if re.search(r"\d", p) and len(p) <= 6:
            out.append(p)
    return out


def _txt(td) -> str:
    return td.get_text(" ", strip=True) if td else ""


def _is_empty_row(cells: list[str]) -> bool:
    return all(not c for c in cells)


def _is_signature_row(cells: list[str]) -> bool:
    """«Заведующая учебным отделом» и подписи — отбрасываем."""
    txt = " ".join(cells).lower()
    return ("заведующ" in txt) or ("__" in txt and len([c for c in cells if c]) <= 2)


def _parse_table(table, fallback_prev_groups: list[str]) -> list[ReplaceRow]:
    rows: list[ReplaceRow] = []
    last_groups = fallback_prev_groups

    trs = table.find_all("tr")
    for i, tr in enumerate(trs):
        tds = tr.find_all("td")
        if not tds:
            continue
        cells = [_txt(td) for td in tds]
        # Шапка таблицы (первая строка)
        if i == 0 and any("групп" in c.lower() for c in cells):
            continue
        if _is_empty_row(cells):
            continue
        if _is_signature_row(cells):
            continue
        # Должно быть 5 колонок. Если меньше — пробуем выровнять.
        while len(cells) < 5:
            cells.append("")
        group_raw, pair, subj_old, subj_new, room = cells[:5]
        groups = _normalize_groups(group_raw)
        if not groups:
            groups = last_groups[:]
        else:
            last_groups = groups[:]
        # Если совсем пустая по содержанию замена и пара — пропускаем
        if not pair and not subj_old and not subj_new:
            continue
        rows.append(ReplaceRow(
            groups=groups,
            pair=pair,
            subject_old=subj_old,
            subject_new=subj_new,
            room=room,
        ))
    return rows


def parse_html(html: str) -> list[ScheduleDay]:
    """Разбирает HTML страницы замен → список ScheduleDay."""
    soup = BeautifulSoup(html, "lxml")
    days: list[ScheduleDay] = []

    h1_list = soup.find_all(["h1", "h2"], string=re.compile(r"Замены", re.I))
    # Иногда текст внутри тега — пробуем альтернативный поиск
    if not h1_list:
        h1_list = [h for h in soup.find_all(["h1", "h2"])
                   if h.get_text(strip=True).lower().startswith("замены")]

    prev_groups: list[str] = []
    for h1 in h1_list:
        date_text = re.sub(r"^Замены на\s*", "", h1.get_text(" ", strip=True),
                           flags=re.I).strip()
        # Ищем ближайшую таблицу после этого заголовка
        table = h1.find_next("table")
        if not table:
            continue
        rows = _parse_table(table, prev_groups)
        if rows:
            prev_groups = rows[-1].groups[:]
        days.append(ScheduleDay(date_text=date_text, rows=rows))
    return days


def content_hash(days: list[ScheduleDay]) -> str:
    """Хэш только по данным (без HTML-обвязки и таймстампов)."""
    data = []
    for d in days:
        data.append({
            "date": d.date_text,
            "rows": [
                f"{','.join(r.groups)}|{r.pair}|{r.subject_old}|{r.subject_new}|{r.room}"
                for r in d.rows
            ],
        })
    raw = json.dumps(data, ensure_ascii=False, sort_keys=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def to_json(days: list[ScheduleDay]) -> str:
    return json.dumps(
        [{"date_text": d.date_text,
          "rows": [asdict(r) for r in d.rows]} for d in days],
        ensure_ascii=False,
    )


def from_json(payload: str) -> list[ScheduleDay]:
    data = json.loads(payload)
    out = []
    for d in data:
        rows = [ReplaceRow(**r) for r in d["rows"]]
        out.append(ScheduleDay(date_text=d["date_text"], rows=rows))
    return out


# ------------------------------------------------------------------
# HTTP

import asyncio
import ssl


async def fetch_html(retries: int = 3) -> tuple[Optional[str], Optional[str]]:
    """Возвращает (html, error). error — короткий код для отображения админу."""
    timeout = aiohttp.ClientTimeout(total=25, connect=10)
    # Сертификат у сайта может быть с устаревшей цепочкой —
    # пробуем сначала со стандартной проверкой, при SSL-ошибке без проверки
    last_err = None
    for attempt in range(1, retries + 1):
        for verify in (True, False):
            connector = aiohttp.TCPConnector(
                ssl=None if verify else ssl._create_unverified_context()
            )
            try:
                async with aiohttp.ClientSession(
                    timeout=timeout, headers=HEADERS, connector=connector
                ) as s:
                    async with s.get(SOURCE_URL, proxy=SCHEDULE_PROXY) as r:
                        body = await r.text(encoding="utf-8", errors="ignore")
                        if r.status == 200 and body:
                            return body, None
                        last_err = f"http_{r.status}"
                        logging.warning("ttzht fetch attempt=%d verify=%s status=%s",
                                        attempt, verify, r.status)
                        break  # status не 200 — не имеет смысла повторять без verify
            except aiohttp.ClientSSLError as e:
                last_err = "ssl_error"
                logging.warning("ttzht ssl error attempt=%d verify=%s: %s",
                                attempt, verify, e)
                # при ssl-ошибке пробуем ещё раз без проверки
                continue
            except asyncio.TimeoutError:
                last_err = "timeout"
                logging.warning("ttzht timeout attempt=%d", attempt)
                break
            except aiohttp.ClientConnectorError as e:
                last_err = "dns_or_connect"
                logging.warning("ttzht connect error attempt=%d: %s", attempt, e)
                break
            except Exception as e:
                last_err = f"unknown:{type(e).__name__}"
                logging.exception("ttzht fetch failed attempt=%d", attempt)
                break
        # Между попытками — пауза
        if attempt < retries:
            await asyncio.sleep(2 * attempt)
    return None, last_err or "unknown"


async def fetch_and_parse() -> tuple[Optional[list[ScheduleDay]], Optional[str]]:
    """Возвращает (days|None, error|None)."""
    html, err = await fetch_html()
    if not html:
        return None, err
    try:
        return parse_html(html), None
    except Exception:
        logging.exception("ttzht parse failed")
        return None, "parse_failed"


# ------------------------------------------------------------------
# Форматирование

_EMPTY = {"", "-->", "—"}
_TIME_RE = re.compile(r"^\d{1,2}[.:]\d{2}$")


def _format_pair(pair: str) -> str:
    """Возвращает оформленный префикс: «🕐 8:00» для времени, «3 пара» для номера."""
    pair = (pair or "").strip()
    if not pair:
        return "•"
    if _TIME_RE.match(pair):
        # 8.00 / 9.00 / 11.00 / 13.00 / 12.30 → 8:00
        norm = pair.replace(".", ":")
        return f"🕐 <b>{norm}</b>"
    # Опечатка вида «1.2» — это «1,2 пара»
    clean = pair.replace(".", ",")
    if "," in clean or "-" in clean:
        return f"<b>{clean}</b> пары"
    return f"<b>{clean}</b> пара"


def _format_subject(text: str) -> str:
    """Чуть аккуратнее оформляем некоторые ключевые случаи."""
    t = text.strip()
    low = t.lower()
    if low.startswith("экзамен"):
        return f"📝 {t}"
    if low.startswith("сам. работа") or "сам. работа обуч" in low or low.startswith("сам.раб"):
        return f"📚 {t}"
    if "свободный день" in low:
        return f"🎉 {t}"
    if "по расписанию" in low:
        return f"📅 {t}"
    return t


def _row_line(r: ReplaceRow) -> str:
    """Одна строка замены — оформляется с учётом частных случаев."""
    pair = _format_pair(r.pair)
    room = f"  📍 ауд. <b>{r.room}</b>" if r.room.strip() else ""
    old = r.subject_old.strip()
    new = r.subject_new.strip()

    # Случай 1: «НЕТ» = пара отменена
    if new.upper() == "НЕТ":
        if old in _EMPTY:
            return f"🚫 {pair}: <b>отменена</b>{room}"
        return f"🚫 {pair}: <b>{old}</b> — отменена{room}"

    # Случай 2: old заполнен, new пустой = возвращается к расписанию
    if old not in _EMPTY and new in _EMPTY:
        return f"♻️ {pair}: <b>{old}</b> — по расписанию{room}"

    # Случай 3: old пустой, new заполнен = добавлена пара
    if old in _EMPTY and new not in _EMPTY:
        return f"➕ {pair}: <b>{_format_subject(new)}</b>{room}"

    # Случай 4: классическая замена old → new
    return f"🔁 {pair}: <s>{old}</s> → <b>{_format_subject(new)}</b>{room}"


def _day_header(date_text: str, group: Optional[str] = None) -> str:
    base = f"📅 <b>{date_text}</b>"
    if group:
        base += f"\n👥 Группа <b>{group}</b>"
    base += "\n━━━━━━━━━━━━━━━"
    return base


def render_for_group(days: list[ScheduleDay], group: str) -> Optional[str]:
    """Сообщение для конкретного подписчика, фильтр по его группе."""
    chunks = []
    for d in days:
        affecting = [r for r in d.rows if r.affects(group)]
        if not affecting:
            continue
        lines = [_day_header(d.date_text, group), ""]
        for r in affecting:
            lines.append(_row_line(r))
        chunks.append("\n".join(lines))
    if not chunks:
        return None
    return "\n\n".join(chunks)


def render_full(days: list[ScheduleDay], limit_rows: int = 200) -> str:
    """Полное расписание (для админ-проверки / общей публикации).
    Группирует строки по группам для компактности."""
    chunks = []
    for d in days:
        # Сгруппируем по «ключу групп» (та же комбинация групп)
        groups_order: list[tuple[str, list[ReplaceRow]]] = []
        last_key = None
        for r in d.rows[:limit_rows]:
            key = ", ".join(r.groups)
            if key != last_key:
                groups_order.append((key, []))
                last_key = key
            groups_order[-1][1].append(r)

        lines = [_day_header(d.date_text)]
        for key, rows in groups_order:
            lines.append(f"\n👥 <b>{key}</b>")
            for r in rows:
                lines.append(_row_line(r))
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks) if chunks else "<i>Замен нет.</i>"


def affected_groups_summary(days: list[ScheduleDay]) -> str:
    """Короткий анонс в чат общаги: даты + кол-во групп."""
    parts = []
    for d in days:
        groups = sorted({g for r in d.rows for g in r.groups})
        parts.append(f"📅 <b>{d.date_text}</b> — затронуто групп: <b>{len(groups)}</b>")
    return "\n".join(parts) if parts else "Изменений нет."


def fetched_age_text(fetched_iso: str) -> str:
    """«5 мин назад» / «2 ч назад» для отметки времени снимка."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(fetched_iso.replace("Z", ""))
        now = datetime.utcnow()
        delta = (now - dt).total_seconds()
    except Exception:
        return fetched_iso
    if delta < 60:
        return "только что"
    if delta < 3600:
        return f"{int(delta // 60)} мин назад"
    if delta < 86400:
        return f"{int(delta // 3600)} ч назад"
    return f"{int(delta // 86400)} дн назад"

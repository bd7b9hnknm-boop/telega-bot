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

def _row_line(r: ReplaceRow) -> str:
    """Одна строка замены — для сообщения в группе/личке."""
    pair_part = f"<b>{r.pair}</b> пара" if r.pair else "•"
    arrow = " → " if r.subject_old not in ("", "-->") else " "
    old_part = "" if r.subject_old in ("", "-->") else f"{r.subject_old}"
    new_part = r.subject_new
    room = f", ауд. <b>{r.room}</b>" if r.room else ""
    return f"▸ {pair_part}: {old_part}{arrow}{new_part}{room}".replace("  ", " ")


def render_for_group(days: list[ScheduleDay], group: str) -> Optional[str]:
    """Сообщение для конкретного подписчика, фильтр по его группе."""
    chunks = []
    for d in days:
        affecting = [r for r in d.rows if r.affects(group)]
        if not affecting:
            continue
        lines = [f"📅 <b>Замены на {d.date_text}</b>", f"👥 Группа <b>{group}</b>", ""]
        for r in affecting:
            lines.append(_row_line(r))
        chunks.append("\n".join(lines))
    if not chunks:
        return None
    return "\n\n".join(chunks)


def render_full(days: list[ScheduleDay], limit_rows: int = 200) -> str:
    """Полное расписание (для админ-проверки / общей публикации)."""
    chunks = []
    for d in days:
        lines = [f"📅 <b>Замены на {d.date_text}</b>", ""]
        for r in d.rows[:limit_rows]:
            grp = ", ".join(r.groups)
            lines.append(f"<b>{grp}</b> · {_row_line(r)}")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks) if chunks else "<i>Замен нет.</i>"


def affected_groups_summary(days: list[ScheduleDay]) -> str:
    """Короткий анонс в чат общаги: даты + кол-во групп."""
    parts = []
    for d in days:
        groups = sorted({g for r in d.rows for g in r.groups})
        parts.append(f"📅 <b>{d.date_text}</b> — затронуто групп: <b>{len(groups)}</b>")
    return "\n".join(parts) if parts else "Изменений нет."

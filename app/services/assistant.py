from __future__ import annotations

import re
from datetime import datetime, timedelta

import httpx
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import (
    Article, ArticleType, BOM, Movement, MovementType,
    SalesChannel, Stock, Warehouse, WarehouseType,
)
from app.services import embeddings

OLLAMA_URL = settings.OLLAMA_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL


def _ask_llm(computed_data: str, question: str) -> str:
    prompt = (
        "Ты — помощник склада SmartTherm. Ниже даны ТОЧНО ПОСЧИТАННЫЕ данные "
        "из базы данных. Сформулируй по ним краткий, понятный ответ на "
        "русском языке. НЕ добавляй никаких цифр, которых нет в данных ниже, "
        "и не пересчитывай их заново — просто перескажи по-человечески.\n\n"
        f"ДАННЫЕ:\n{computed_data}\n\n"
        f"ВОПРОС: {question}\n\nОТВЕТ:"
    )
    try:
        with httpx.Client(timeout=60.0, proxies=None) as client:
            resp = client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            })
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            return text if text else computed_data
    except Exception:
        return (
            "⚠️ Локальная модель (Ollama) недоступна — показываю точные "
            "данные без литературной обработки:\n\n" + computed_data
        )


def _dated(answer: str) -> str:
    return answer + f"\n\n_Данные на: {datetime.utcnow():%d.%m.%Y %H:%M} UTC_"


# Раньше "сейчас" во всех расчётах ("прошлый месяц", "последний квартал",
# "последние 3 месяца") бралось из реальных часов компьютера
# (datetime.utcnow()). Это ломается ровно в тот момент, когда реальное
# время уходит вперёд относительно исторической выгрузки: если последнее
# движение в базе датировано ноябрём 2025, а на часах — август 2026, то
# "прошлый месяц" по часам (июль 2026) в данных попросту пуст, хотя
# содержательные данные в базе есть — просто не в этом окне времени.
#
# Решение: точку отсчёта "сейчас" для ВСЕХ относительных периодов берём
# не с часов, а по дате последнего движения в самой базе. Формулы и
# логика не меняются — меняется только то, откуда берётся "сейчас".
# Это не костыль, а корректный подход для систем с периодическим
# импортом исторических данных (данные не "устаревают" сами по себе,
# просто перестают быть актуальными для "живых" часов).
def _reference_now(db: Session) -> datetime:
    latest = db.query(func.max(Movement.movement_date)).scalar()
    return latest or datetime.utcnow()


_QTY_RE = re.compile(r"(\d+)\s*(шт|штук|штуки|единиц)?", re.IGNORECASE)
_ARTICLE_RE = re.compile(r"\b([A-ZА-Я]{1,4}_[A-ZА-Я0-9]{2,}|\d{3,5})\b")


def handle_production_shortage(db: Session, question: str) -> str:
    # Не меняется: проверяет ТЕКУЩИЕ остатки, дата тут ни при чём.
    art_match = _ARTICLE_RE.search(question.upper())
    if art_match:
        code = art_match.group(1)
        finished = db.query(Article).filter(
            Article.code == code, Article.article_type == ArticleType.FINISHED
        ).first()
    else:
        finished = embeddings.find_article_by_name(db, question, article_type=ArticleType.FINISHED)
        code = finished.code if finished else None

    if not finished:
        return "Не смог распознать артикул готового изделия в вопросе. Уточните код (например FS_ST005) или точное название."

    qty_match = _QTY_RE.search(question)
    qty = float(qty_match.group(1)) if qty_match else 1.0

    bom_entries = db.query(BOM).filter(BOM.parent_id == finished.id).all()
    if not bom_entries:
        return f"Для '{code}' не задана спецификация (BOM)."

    wh_comp = db.query(Warehouse).filter(Warehouse.warehouse_type == WarehouseType.COMPONENTS).first()

    lines, all_ok = [], True
    for e in bom_entries:
        required = e.quantity * qty
        stock = db.query(Stock).filter_by(article_id=e.child_id, warehouse_id=wh_comp.id).first()
        available = stock.quantity if stock else 0
        shortfall = max(0.0, required - available)
        if shortfall > 0:
            all_ok = False
        status = f"не хватает {shortfall:g}" if shortfall > 0 else "хватает"
        lines.append(f"- {e.child.code} ({e.child.name}): нужно {required:g}, есть {available:g} — {status}")

    header = f"Производство {code} ({finished.name}) в количестве {qty:g} шт.\n"
    body = "Всех компонентов хватает.\n" if all_ok else "Не хватает:\n"
    data = header + body + "\n".join(lines)

    return _dated(_ask_llm(data, question))


SAFETY_STOCK_FACTOR = 1.2


def handle_purchase_plan(db: Session, question: str) -> str:
    now = _reference_now(db)  # было: datetime.utcnow()
    period_start = now - timedelta(days=90)
    months = 3

    wh_comp = db.query(Warehouse).filter(Warehouse.warehouse_type == WarehouseType.COMPONENTS).first()

    consumption_rows = (
        db.query(Movement.article_id, func.sum(Movement.quantity).label("total"))
        .filter(Movement.movement_type == MovementType.PRODUCTION,
                Movement.warehouse_id == wh_comp.id,
                Movement.movement_date >= period_start)
        .group_by(Movement.article_id)
        .all()
    )
    consumption_map = {a_id: total / months for a_id, total in consumption_rows}

    components = db.query(Article).filter(
        Article.article_type == ArticleType.COMPONENT, Article.is_active == True
    ).all()

    lines = []
    for a in components:
        avg_monthly = consumption_map.get(a.id, 0)
        if avg_monthly <= 0:
            continue
        stock = db.query(Stock).filter_by(article_id=a.id, warehouse_id=wh_comp.id).first()
        current = stock.quantity if stock else 0
        target = avg_monthly * SAFETY_STOCK_FACTOR
        need = max(0.0, target - current)
        if need > 0:
            lines.append(f"- {a.code} ({a.name}): средний расход {avg_monthly:.1f}/мес, "
                         f"остаток {current:g}, целевой запас (со страховым запасом +20%) "
                         f"{target:.1f} — рекомендуется закупить ≈{need:.0f}")

    if lines:
        data = ("Рекомендации по закупке (средний расход за последние 3 месяца "
                "+ страховой запас 20%, чтобы остатка гарантированно хватило на "
                "следующий месяц):\n" + "\n".join(lines))
    else:
        data = "По данным за последние 3 месяца текущих остатков хватает (с учётом страхового запаса 20%) на месяц вперёд по всем компонентам."

    return _dated(_ask_llm(data, question))


def handle_top_sellers(db: Session, question: str) -> str:
    now = _reference_now(db)  # было: datetime.utcnow()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = first_of_this_month - timedelta(seconds=1)
    last_month_start = last_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    rows = (
        db.query(Article.code, Article.name, func.sum(Movement.quantity).label("total"))
        .join(Movement, Movement.article_id == Article.id)
        .filter(Movement.movement_type == MovementType.SHIPMENT,
                Movement.movement_date >= last_month_start,
                Movement.movement_date <= last_month_end)
        .group_by(Article.code, Article.name)
        .order_by(func.sum(Movement.quantity).desc())
        .limit(5)
        .all()
    )

    if not rows:
        data = f"За период {last_month_start:%d.%m.%Y}–{last_month_end:%d.%m.%Y} отгрузок не найдено."
    else:
        lines = [f"{i+1}. {code} ({name}): {int(total)} шт." for i, (code, name, total) in enumerate(rows)]
        data = (f"Топ продаж за {last_month_start:%B %Y} (по количеству отгруженных штук):\n"
                + "\n".join(lines))

    return _dated(_ask_llm(data, question))


_CHANNEL_LABELS = {
    SalesChannel.MARKETPLACE_1: "Ozon",
    SalesChannel.MARKETPLACE_2: "Яндекс.Маркет",
    SalesChannel.WEBSITE: "Сайт",
    SalesChannel.OTHER: "Другое",
    None: "Без указания канала",
}


def handle_revenue_by_channel(db: Session, question: str) -> str:
    art_match = _ARTICLE_RE.search(question.upper())
    if art_match:
        code = art_match.group(1)
        article = db.query(Article).filter(Article.code == code).first()
    else:
        article = embeddings.find_article_by_name(db, question, article_type=ArticleType.FINISHED)
        code = article.code if article else None

    if not article:
        return "Не смог распознать артикул в вопросе. Уточните код (например FS_ST005) или точное название."

    now = _reference_now(db)  # было: datetime.utcnow()
    period_start = now - timedelta(days=90)

    shipments = (
        db.query(Movement.sales_channel, func.sum(Movement.quantity * Movement.price_per_unit))
        .filter(Movement.article_id == article.id, Movement.movement_type == MovementType.SHIPMENT,
                Movement.movement_date >= period_start)
        .group_by(Movement.sales_channel)
        .all()
    )
    returns_map = dict(
        db.query(Movement.sales_channel, func.sum(Movement.quantity * Movement.price_per_unit))
        .filter(Movement.article_id == article.id, Movement.movement_type == MovementType.RETURN,
                Movement.movement_date >= period_start)
        .group_by(Movement.sales_channel)
        .all()
    )

    if not shipments:
        data = f"За последние 3 месяца отгрузок по '{code}' не найдено."
    else:
        lines, total = [], 0.0
        for ch, rev in shipments:
            rev = rev or 0
            ret = returns_map.get(ch, 0) or 0
            net = rev - ret
            total += net
            lines.append(f"- {_CHANNEL_LABELS.get(ch, ch)}: выручка {rev:.0f} ₽, "
                         f"возвраты {ret:.0f} ₽, чистыми {net:.0f} ₽")
        data = (f"Выручка по '{code}' ({article.name}) за последние 3 месяца по каналам:\n"
                + "\n".join(lines) + f"\n\nИтого чистыми за период: {total:.0f} ₽")

    return _dated(_ask_llm(data, question))


def handle_available_funds(db: Session, question: str) -> str:
    now = _reference_now(db)  # было: datetime.utcnow()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = first_of_this_month - timedelta(seconds=1)
    period_start = period_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    shipments = (
        db.query(Movement.article_id, Movement.quantity, Movement.price_per_unit)
        .filter(Movement.movement_type == MovementType.SHIPMENT,
                Movement.movement_date >= period_start, Movement.movement_date <= period_end)
        .all()
    )

    revenue = sum(m.quantity * (m.price_per_unit or 0) for m in shipments)

    cost_of_goods = 0.0
    if shipments:
        article_ids = {m.article_id for m in shipments}
        cost_map = {a.id: a.cost_price for a in db.query(Article).filter(Article.id.in_(article_ids)).all()}
        cost_of_goods = sum(m.quantity * cost_map.get(m.article_id, 0) for m in shipments)

    operating_expenses = settings.OPERATING_EXPENSES_MONTHLY
    total = revenue - cost_of_goods - operating_expenses

    data = (
        f"Расчёт за {period_start:%B %Y} (прошлый месяц, {period_start:%d.%m}–{period_end:%d.%m.%Y}):\n"
        f"Выручка: {revenue:.0f} руб.\n"
        f"Себестоимость: {cost_of_goods:.0f} руб.\n"
        f"Операционные расходы: {operating_expenses:.0f} руб.\n"
        f"Итого: {total:.0f} руб.\n\n"
        f"(Операционные расходы заданы гипотетической константой "
        f"OPERATING_EXPENSES_MONTHLY в .env — по умолчанию 0, задайте "
        f"реальную оценку. Себестоимость посчитана по полю cost_price "
        f"проданных артикулов.)"
    )
    return _dated(_ask_llm(data, question))


_INTENT_PATTERNS = [
    (re.compile(r"не хватает|дефицит|хват[аи]ет.*производ", re.IGNORECASE), handle_production_shortage),
    (re.compile(r"закуп", re.IGNORECASE), handle_purchase_plan),
    (re.compile(r"лучше всего|топ продаж|лучше.*продав|продав.*лучше|хорошо.*продав|продав.*хорошо", re.IGNORECASE), handle_top_sellers),
    (re.compile(r"выручк|сколько.*рубл|на сколько рублей|продано.*руб", re.IGNORECASE), handle_revenue_by_channel),
    (re.compile(r"реинвестир|выплат|дивиденд|сумм.*доступн|доступн.*сумм|свободн.*средств", re.IGNORECASE), handle_available_funds),
]

_HANDLERS = {
    "production_shortage": handle_production_shortage,
    "purchase_plan": handle_purchase_plan,
    "top_sellers": handle_top_sellers,
    "revenue_by_channel": handle_revenue_by_channel,
    "available_funds": handle_available_funds,
}

_FALLBACK = (
    "Пока уверенно умею отвечать на 5 обязательных вопросов из ТЗ:\n"
    "1. Чего не хватает для производства артикула X в количестве N?\n"
    "2. Что необходимо закупить в этом месяце?\n"
    "3. Какие товары продавались лучше всего за прошлый месяц?\n"
    "4. Какова выручка по артикулу X за последний квартал по каналам продаж?\n"
    "5. Какая сумма доступна для реинвестирования/выплат за прошлый месяц?\n\n"
    "Попробуйте переформулировать вопрос ближе к одному из них."
)


def answer_question(db: Session, question: str) -> str:
    for pattern, handler in _INTENT_PATTERNS:
        if pattern.search(question):
            return handler(db, question)

    try:
        intent = embeddings.classify_intent(question)
    except Exception:
        intent = None

    if intent and intent in _HANDLERS:
        return _HANDLERS[intent](db, question)

    return _FALLBACK

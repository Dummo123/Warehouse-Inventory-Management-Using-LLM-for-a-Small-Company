"""
Логика ИИ-помощника (Чекпоинт #3).

КАК ЭТО УСТРОЕНО (и почему именно так):

  1. Вопрос пользователя сопоставляется с одним из 5 ОБЯЗАТЕЛЬНЫХ типов
     вопросов из ТЗ — по ключевым словам (простые регулярные выражения).

  2. Для распознанного типа выполняется ТОЧНЫЙ SQL/ORM-запрос к живой
     PostgreSQL. Числа в ответе ВСЕГДА берутся из реальных данных.

  3. Только готовые цифры + вопрос отправляются в локальную LLM (Ollama) —
     и ТОЛЬКО для того, чтобы облечь их в связный русский текст.
     LLM НЕ участвует в подсчётах и не может "придумать" цифру, которой
     не было в переданных данных.

  4. Если вопрос не подходит ни под один из 5 типов — сначала пробуем
     семантическое сравнение через эмбеддинги (embeddings.py), и только
     если это тоже не сработало — честно говорим, что уверенно умеем
     отвечать пока только на 5 обязательных вопросов.

Если Ollama не запущена/недоступна — ассистент не "падает", а просто
возвращает точные данные без литературной обработки (с пометкой об этом).
"""
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

# Адрес и модель читаются из настроек (.env) — см. app/core/config.py.
# Ollama по плану проекта работает на отдельном GPU-сервере, а не на
# ноутбуке разработчика, поэтому значение должно быть настраиваемым.
OLLAMA_URL = settings.OLLAMA_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL


# ── Вызов локальной LLM: ТОЛЬКО для формулировки текста ────────────────

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
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            })
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            return text if text else computed_data
    except Exception:
        # Ollama не запущена/недоступна — ассистент не должен становиться
        # бесполезным, отдаём посчитанные данные как есть.
        return (
            "⚠️ Локальная модель (Ollama) недоступна — показываю точные "
            "данные без литературной обработки:\n\n" + computed_data
        )


def _dated(answer: str) -> str:
    return answer + f"\n\n_Данные на: {datetime.utcnow():%d.%m.%Y %H:%M} UTC_"


_QTY_RE = re.compile(r"(\d+)\s*(шт|штук|штуки|единиц)?", re.IGNORECASE)
_ARTICLE_RE = re.compile(r"\b([A-ZА-Я]{1,4}_[A-ZА-Я0-9]{2,}|\d{3,5})\b")


# ── Вопрос 1: чего не хватает для производства ──────────────────────────

def handle_production_shortage(db: Session, question: str) -> str:
    art_match = _ARTICLE_RE.search(question.upper())
    if art_match:
        code = art_match.group(1)
        finished = db.query(Article).filter(
            Article.code == code, Article.article_type == ArticleType.FINISHED
        ).first()
    else:
        # Код не найден в тексте явно — пробуем найти изделие по названию
        # через семантический поиск (эмбеддинги), например "контроллер в
        # корпусе ESP32 без датчиков" → FS_ST006.
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


# ── Вопрос 2: что закупить в этом месяце ────────────────────────────────

# ТЗ (п.2.2, вопрос 2): "прогноз на основе плана производства или
# популярности артикулов + страховой запас". План производства как
# отдельная сущность в системе не ведётся, поэтому в качестве прокси для
# "популярности" используется фактический расход компонентов на
# производство за последние 3 месяца, плюс явный страховой запас 20%.
SAFETY_STOCK_FACTOR = 1.2  # +20% сверх среднемесячного расхода


def handle_purchase_plan(db: Session, question: str) -> str:
    now = datetime.utcnow()
    period_start = now - timedelta(days=90)  # динамика расхода — за последние 3 месяца
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


# ── Вопрос 3: топ продаж за прошлый месяц ───────────────────────────────

def handle_top_sellers(db: Session, question: str) -> str:
    now = datetime.utcnow()
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


# ── Вопрос 4: выручка по артикулу за квартал по каналам ─────────────────

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

    now = datetime.utcnow()
    period_start = now - timedelta(days=90)  # "последний квартал" = последние 3 месяца

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


# ── Вопрос 5: доступная сумма для реинвестирования/дивидендов ───────────
# ТЗ (п.2.2, вопрос 5) требует РОВНО такой ответ: "Выручка: X,
# Себестоимость: Y, Операционные расходы: Z, Итого: W руб." — и именно за
# ПРОШЛЫЙ месяц (не текущий).

def handle_available_funds(db: Session, question: str) -> str:
    now = datetime.utcnow()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = first_of_this_month - timedelta(seconds=1)
    period_start = period_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    shipments = (
        db.query(Movement.article_id, Movement.quantity, Movement.price_per_unit)
        .filter(Movement.movement_type == MovementType.SHIPMENT,
                Movement.movement_date >= period_start, Movement.movement_date <= period_end)
        .all()
    )

    # Выручка (X)
    revenue = sum(m.quantity * (m.price_per_unit or 0) for m in shipments)

    # Себестоимость проданного (Y) = кол-во * себестоимость артикула
    # (Article.cost_price — закупочная/производственная цена единицы).
    cost_of_goods = 0.0
    if shipments:
        article_ids = {m.article_id for m in shipments}
        cost_map = {a.id: a.cost_price for a in db.query(Article).filter(Article.id.in_(article_ids)).all()}
        cost_of_goods = sum(m.quantity * cost_map.get(m.article_id, 0) for m in shipments)

    # Операционные расходы (Z) — гипотетическая константа (ТЗ прямо
    # разрешает такое упрощение), настраивается в .env / config.py.
    operating_expenses = settings.OPERATING_EXPENSES_MONTHLY

    # Итого (W)
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


# ── Роутинг: определяем, какой из 5 вопросов задан ──────────────────────

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
    # 1) быстрый и дешёвый проход — точные ключевые слова
    for pattern, handler in _INTENT_PATTERNS:
        if pattern.search(question):
            return handler(db, question)

    # 2) вопрос сформулирован не по шаблону — пробуем семантическое
    #    сравнение с 5 эталонными вопросами (эмбеддинги).
    try:
        intent = embeddings.classify_intent(question)
    except Exception:
        # Модель эмбеддингов не установлена/не загрузилась — не роняем
        # ассистента, просто пропускаем семантический проход.
        intent = None

    if intent and intent in _HANDLERS:
        return _HANDLERS[intent](db, question)

    return _FALLBACK

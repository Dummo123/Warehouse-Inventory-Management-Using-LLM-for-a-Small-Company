"""Reports — аналог /export_reports из бота."""
import io
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Stock, Movement, Article, Warehouse, User, ArticleType

router = APIRouter(prefix="/reports", tags=["reports"])


def _col_widths(writer, df: pd.DataFrame, sheet_name: str):
    ws = writer.sheets[sheet_name]
    for i, col in enumerate(df.columns):
        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 4
        ws.column_dimensions[chr(65 + i)].width = min(max_len, 60)


@router.get("/export")
def export_reports(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Генерация Excel-отчёта (аналог /export_reports).
    Листы: Stock, Movements, Semi-Finished Products, Products.
    """
    # Stock
    stock_rows = (
        db.query(Stock).join(Article).join(Warehouse)
        .filter(Article.is_active == True)
        .order_by(Article.code).all()
    )
    stock_data = [{
        "Артикул": s.article.code,
        "Наименование": s.article.name,
        "Тип": s.article.article_type,
        "Склад": s.warehouse.name,
        "Остаток": s.quantity,
        "Цена": s.article.cost_price,
        "Стоимость остатка": round(s.quantity * s.article.cost_price, 2),
    } for s in stock_rows]

    # Movements
    mv_q = db.query(Movement).join(Article).join(Warehouse)
    if date_from:
        mv_q = mv_q.filter(Movement.movement_date >= date_from)
    if date_to:
        mv_q = mv_q.filter(Movement.movement_date <= date_to)
    movements = mv_q.order_by(Movement.movement_date.desc()).all()
    movement_data = [{
        "Дата": m.movement_date.strftime("%Y-%m-%d %H:%M"),
        "Артикул": m.article.code,
        "Наименование": m.article.name,
        "Тип операции": m.movement_type,
        "Поступление": m.quantity if m.movement_type == "receipt" else 0,
        "Отгрузка": m.quantity if m.movement_type == "shipment" else 0,
        "Производство": m.quantity if m.movement_type == "production" else 0,
        "Комментарий": m.comment or "",
    } for m in movements]

    # Semi-finished
    sf_rows = db.query(Article).filter(
        Article.article_type == ArticleType.COMPONENT,
        Article.is_active == True,
    ).order_by(Article.code).all()
    sf_data = [{
        "Артикул": a.code, "Наименование": a.name,
        "Стоимость": a.cost_price, "Ответственный": a.responsible or "",
        "Комментарий": a.comment or "",
    } for a in sf_rows]

    # Products + BOM
    fin_rows = db.query(Article).filter(
        Article.article_type == ArticleType.FINISHED,
        Article.is_active == True,
    ).order_by(Article.code).all()
    prod_data = [{
        "Артикул": a.code,
        "Наименование": a.name,
        "Состав": ", ".join(
            f"{b.child.code} ({b.quantity})" for b in a.bom_parent
        ),
    } for a in fin_rows]

    # Write to in-memory Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for df_data, sheet in [
            (stock_data, "Stock"),
            (movement_data, "Movements"),
            (sf_data, "Semi-Finished Products"),
            (prod_data, "Products"),
        ]:
            df = pd.DataFrame(df_data)
            df.to_excel(writer, sheet_name=sheet, index=False)
            _col_widths(writer, df, sheet)

    output.seek(0)
    filename = f"warehouse_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Stock, Article, Warehouse, ArticleType, WarehouseType, User
from app.schemas.schemas import StockOut

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("", response_model=List[StockOut])
def get_stock(
    warehouse_type: Optional[WarehouseType] = None,
    article_type: Optional[ArticleType] = None,
    low_stock: Optional[float] = Query(None, description="Показать только артикулы с остатком ниже указанного"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Текущие остатки на складах.
    Аналог /watch_stock из бота — но для всех артикулов.
    """
    q = db.query(Stock).join(Article).join(Warehouse).filter(Article.is_active == True)

    if warehouse_type:
        q = q.filter(Warehouse.warehouse_type == warehouse_type)
    if article_type:
        q = q.filter(Article.article_type == article_type)
    if low_stock is not None:
        q = q.filter(Stock.quantity <= low_stock)

    entries = q.order_by(Article.code).all()

    return [
        StockOut(
            article_code=s.article.code,
            article_name=s.article.name,
            article_type=s.article.article_type,
            warehouse_name=s.warehouse.name,
            quantity=s.quantity,
            cost_price=s.article.cost_price,
            total_value=s.quantity * s.article.cost_price,
        )
        for s in entries
    ]


@router.get("/finished", response_model=List[StockOut])
def get_finished_stock(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Быстрый просмотр остатков готовых изделий (FS_*)."""
    entries = (
        db.query(Stock)
        .join(Article)
        .join(Warehouse)
        .filter(
            Article.is_active == True,
            Article.article_type == ArticleType.FINISHED,
            Warehouse.warehouse_type == WarehouseType.FINISHED_GOODS,
        )
        .order_by(Article.code)
        .all()
    )
    return [
        StockOut(
            article_code=s.article.code,
            article_name=s.article.name,
            article_type=s.article.article_type,
            warehouse_name=s.warehouse.name,
            quantity=s.quantity,
            cost_price=s.article.cost_price,
            total_value=s.quantity * s.article.cost_price,
        )
        for s in entries
    ]

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.models.models import (
    Movement, MovementType, Article, ArticleType,
    Stock, Warehouse, WarehouseType, ProductionBatch, BOM, User
)
from app.schemas.schemas import MovementCreate, MovementOut, ProductionCreate, ProductionOut

router = APIRouter(prefix="/movements", tags=["movements"])


def _get_stock(db: Session, article_id: int, warehouse_id: int) -> Stock:
    s = db.query(Stock).filter_by(article_id=article_id, warehouse_id=warehouse_id).first()
    if not s:
        s = Stock(article_id=article_id, warehouse_id=warehouse_id, quantity=0)
        db.add(s)
        db.flush()
    return s


def _get_warehouse(db: Session, wh_type: WarehouseType) -> Warehouse:
    wh = db.query(Warehouse).filter(Warehouse.warehouse_type == wh_type).first()
    if not wh:
        raise HTTPException(status_code=500, detail=f"Склад типа '{wh_type}' не найден в БД")
    return wh


@router.get("", response_model=List[MovementOut])
def list_movements(
    article_code: Optional[str] = None,
    movement_type: Optional[MovementType] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Movement).join(Article).join(Warehouse)
    if article_code:
        q = q.filter(Article.code == article_code)
    if movement_type:
        q = q.filter(Movement.movement_type == movement_type)
    if date_from:
        q = q.filter(Movement.movement_date >= date_from)
    if date_to:
        q = q.filter(Movement.movement_date <= date_to)

    movements = q.order_by(Movement.movement_date.desc()).offset(offset).limit(limit).all()

    return [
        MovementOut(
            id=m.id,
            article_code=m.article.code,
            article_name=m.article.name,
            warehouse_name=m.warehouse.name,
            movement_type=m.movement_type,
            quantity=m.quantity,
            price_per_unit=m.price_per_unit,
            sales_channel=m.sales_channel,
            comment=m.comment,
            movement_date=m.movement_date,
        )
        for m in movements
    ]


@router.post("/receipt", response_model=MovementOut, status_code=201)
def receipt(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """Поступление товара на склад компонентов (/po)."""
    article = db.query(Article).filter(
        Article.code == payload.article_code,
        Article.is_active == True
    ).first()
    if not article:
        raise HTTPException(404, f"Артикул '{payload.article_code}' не найден")

    wh = _get_warehouse(db, WarehouseType.COMPONENTS)
    stock = _get_stock(db, article.id, wh.id)
    stock.quantity += payload.quantity

    mv = Movement(
        article_id=article.id,
        warehouse_id=wh.id,
        movement_type=MovementType.RECEIPT,
        quantity=payload.quantity,
        price_per_unit=payload.price_per_unit or article.cost_price,
        comment=payload.comment,
        movement_date=payload.movement_date or datetime.utcnow(),
        user_id=current_user.id,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    return MovementOut(
        id=mv.id, article_code=article.code, article_name=article.name,
        warehouse_name=wh.name, movement_type=mv.movement_type,
        quantity=mv.quantity, price_per_unit=mv.price_per_unit,
        sales_channel=mv.sales_channel, comment=mv.comment,
        movement_date=mv.movement_date,
    )


@router.post("/shipment", response_model=MovementOut, status_code=201)
def shipment(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """Отгрузка готового товара со склада (/ot)."""
    article = db.query(Article).filter(
        Article.code == payload.article_code,
        Article.is_active == True
    ).first()
    if not article:
        raise HTTPException(404, f"Артикул '{payload.article_code}' не найден")

    wh = _get_warehouse(db, WarehouseType.FINISHED_GOODS)
    stock = _get_stock(db, article.id, wh.id)

    if stock.quantity < payload.quantity:
        raise HTTPException(400, f"Недостаточно товара. На складе: {stock.quantity} шт.")

    stock.quantity -= payload.quantity

    mv = Movement(
        article_id=article.id,
        warehouse_id=wh.id,
        movement_type=MovementType.SHIPMENT,
        quantity=payload.quantity,
        price_per_unit=payload.price_per_unit or article.cost_price,
        sales_channel=payload.sales_channel,
        comment=payload.comment,
        movement_date=payload.movement_date or datetime.utcnow(),
        user_id=current_user.id,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    return MovementOut(
        id=mv.id, article_code=article.code, article_name=article.name,
        warehouse_name=wh.name, movement_type=mv.movement_type,
        quantity=mv.quantity, price_per_unit=mv.price_per_unit,
        sales_channel=mv.sales_channel, comment=mv.comment,
        movement_date=mv.movement_date,
    )


@router.post("/production", response_model=ProductionOut, status_code=201)
def production(
    payload: ProductionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Производство (/pr) — конвертация комплектующих в готовое изделие.
    Проверяет наличие всех компонентов по BOM, затем списывает их
    и оприходует готовые изделия — всё в одной транзакции.
    """
    finished = db.query(Article).filter(
        Article.code == payload.finished_article_code,
        Article.is_active == True,
        Article.article_type == ArticleType.FINISHED,
    ).first()
    if not finished:
        raise HTTPException(404, f"Готовое изделие '{payload.finished_article_code}' не найдено")

    bom_entries = db.query(BOM).filter(BOM.parent_id == finished.id).all()
    if not bom_entries:
        raise HTTPException(400, f"BOM для '{payload.finished_article_code}' не задан")

    wh_comp = _get_warehouse(db, WarehouseType.COMPONENTS)
    wh_fin = _get_warehouse(db, WarehouseType.FINISHED_GOODS)

    # проверяем что всего хватает прежде чем что-то трогать
    shortages = []
    for entry in bom_entries:
        required = entry.quantity * payload.quantity
        stock = _get_stock(db, entry.child_id, wh_comp.id)
        if stock.quantity < required:
            shortages.append(
                f"{entry.child.code} ({entry.child.name}): "
                f"нужно {required}, есть {stock.quantity}"
            )
    if shortages:
        raise HTTPException(
            status_code=400,
            detail="Недостаточно компонентов:\n" + "\n".join(shortages),
        )

    batch = ProductionBatch(
        finished_article_id=finished.id,
        quantity_produced=payload.quantity,
        user_id=current_user.id,
        comment=payload.comment,
    )
    db.add(batch)
    db.flush()

    components_deducted = []
    for entry in bom_entries:
        required = entry.quantity * payload.quantity
        stock = _get_stock(db, entry.child_id, wh_comp.id)
        stock.quantity -= required

        db.add(Movement(
            article_id=entry.child_id,
            warehouse_id=wh_comp.id,
            movement_type=MovementType.PRODUCTION,
            quantity=required,
            comment=f"Производство {payload.quantity} шт. {finished.code}",
            movement_date=datetime.utcnow(),
            user_id=current_user.id,
            production_batch_id=batch.id,
        ))
        components_deducted.append({
            "code": entry.child.code,
            "name": entry.child.name,
            "deducted": required,
            "remaining": stock.quantity,
        })

    fin_stock = _get_stock(db, finished.id, wh_fin.id)
    fin_stock.quantity += payload.quantity

    db.add(Movement(
        article_id=finished.id,
        warehouse_id=wh_fin.id,
        movement_type=MovementType.PRODUCTION,
        quantity=payload.quantity,
        comment=payload.comment,
        movement_date=datetime.utcnow(),
        user_id=current_user.id,
        production_batch_id=batch.id,
    ))
    db.commit()

    return ProductionOut(
        batch_id=batch.id,
        finished_article_code=finished.code,
        finished_article_name=finished.name,
        quantity_produced=payload.quantity,
        components_deducted=components_deducted,
        comment=payload.comment,
        produced_at=batch.produced_at,
    )


@router.post("/return", response_model=MovementOut, status_code=201)
def return_goods(
    payload: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """Возврат готового товара от клиента."""
    article = db.query(Article).filter(
        Article.code == payload.article_code,
        Article.is_active == True
    ).first()
    if not article:
        raise HTTPException(404, f"Артикул '{payload.article_code}' не найден")

    wh = _get_warehouse(db, WarehouseType.FINISHED_GOODS)
    stock = _get_stock(db, article.id, wh.id)
    stock.quantity += payload.quantity

    mv = Movement(
        article_id=article.id,
        warehouse_id=wh.id,
        movement_type=MovementType.RETURN,
        quantity=payload.quantity,
        sales_channel=payload.sales_channel,
        comment=payload.comment,
        movement_date=payload.movement_date or datetime.utcnow(),
        user_id=current_user.id,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    return MovementOut(
        id=mv.id, article_code=article.code, article_name=article.name,
        warehouse_name=wh.name, movement_type=mv.movement_type,
        quantity=mv.quantity, price_per_unit=mv.price_per_unit,
        sales_channel=mv.sales_channel, comment=mv.comment,
        movement_date=mv.movement_date,
    )

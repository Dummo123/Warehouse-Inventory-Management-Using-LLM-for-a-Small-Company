from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_operator, require_admin
from app.db.session import get_db
from app.models.models import Article, ArticleType, BOM, Stock, Warehouse, WarehouseType, User
from app.schemas.schemas import ArticleCreate, ArticleOut, ArticleUpdate, BOMEntry, BOMEntryOut

router = APIRouter(prefix="/articles", tags=["articles"])


def _get_or_404(db: Session, code: str) -> Article:
    a = db.query(Article).filter(Article.code == code, Article.is_active == True).first()
    if not a:
        raise HTTPException(status_code=404, detail=f"Артикул '{code}' не найден")
    return a


@router.get("", response_model=List[ArticleOut])
def list_articles(
    article_type: Optional[ArticleType] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Article).filter(Article.is_active == True)
    if article_type:
        q = q.filter(Article.article_type == article_type)
    return q.order_by(Article.code).all()


@router.get("/{code}", response_model=ArticleOut)
def get_article(code: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_or_404(db, code)


@router.post("", response_model=ArticleOut, status_code=201)
def create_article(
    payload: ArticleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_operator),
):
    if db.query(Article).filter(Article.code == payload.code).first():
        raise HTTPException(status_code=400, detail="Артикул уже существует")

    article = Article(**payload.model_dump())
    db.add(article)

    # Automatically add to the right warehouse stock at 0
    wh_type = WarehouseType.FINISHED_GOODS if payload.article_type == ArticleType.FINISHED else WarehouseType.COMPONENTS
    wh = db.query(Warehouse).filter(Warehouse.warehouse_type == wh_type).first()
    if wh:
        db.flush()  # get article.id
        stock = Stock(article_id=article.id, warehouse_id=wh.id, quantity=0)
        db.add(stock)

    db.commit()
    db.refresh(article)
    return article


@router.patch("/{code}", response_model=ArticleOut)
def update_article(
    code: str,
    payload: ArticleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_operator),
):
    article = _get_or_404(db, code)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return article


@router.delete("/{code}", status_code=204)
def delete_article(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_operator),
):
    article = _get_or_404(db, code)
    article.is_active = False
    db.commit()


# BOM endpoints
@router.get("/{code}/bom", response_model=List[BOMEntryOut])
def get_bom(code: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    parent = _get_or_404(db, code)
    entries = db.query(BOM).filter(BOM.parent_id == parent.id).all()
    return [
        BOMEntryOut(
            child_id=e.child_id,
            child_code=e.child.code,
            child_name=e.child.name,
            quantity=e.quantity,
        )
        for e in entries
    ]


@router.put("/{code}/bom", response_model=List[BOMEntryOut])
def set_bom(
    code: str,
    entries: List[BOMEntry],
    db: Session = Depends(get_db),
    _: User = Depends(require_operator),
):
    """Replace the full BOM for a finished product."""
    parent = _get_or_404(db, code)
    if parent.article_type != ArticleType.FINISHED:
        raise HTTPException(status_code=400, detail="BOM можно задать только для готового изделия")

    # Delete existing BOM
    db.query(BOM).filter(BOM.parent_id == parent.id).delete()

    result = []
    for entry in entries:
        child = db.query(Article).filter(Article.code == entry.child_code).first()
        if not child:
            raise HTTPException(status_code=404, detail=f"Компонент '{entry.child_code}' не найден")
        bom = BOM(parent_id=parent.id, child_id=child.id, quantity=entry.quantity)
        db.add(bom)
        result.append(BOMEntryOut(
            child_id=child.id,
            child_code=child.code,
            child_name=child.name,
            quantity=entry.quantity,
        ))

    db.commit()
    return result

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator
from app.models.models import ArticleType, MovementType, UserRole, SalesChannel


# ── Article ──────────────────────────────────────────────────────────────────

class ArticleBase(BaseModel):
    code: str
    name: str
    article_type: ArticleType
    unit: str = "шт"
    cost_price: float = 0.0
    responsible: Optional[str] = None
    comment: Optional[str] = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[float] = None
    responsible: Optional[str] = None
    comment: Optional[str] = None
    is_active: Optional[bool] = None


class ArticleOut(ArticleBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── BOM ───────────────────────────────────────────────────────────────────────

class BOMEntry(BaseModel):
    child_code: str      # артикул компонента
    quantity: float


class BOMEntryOut(BaseModel):
    child_id: int
    child_code: str
    child_name: str
    quantity: float

    model_config = {"from_attributes": True}


# ── Stock ─────────────────────────────────────────────────────────────────────

class StockOut(BaseModel):
    article_code: str
    article_name: str
    article_type: ArticleType
    warehouse_name: str
    quantity: float
    cost_price: float
    total_value: float

    model_config = {"from_attributes": True}


# ── Movement ──────────────────────────────────────────────────────────────────

class MovementCreate(BaseModel):
    article_code: str
    movement_type: MovementType
    quantity: float
    price_per_unit: Optional[float] = None
    sales_channel: Optional[SalesChannel] = None
    comment: Optional[str] = None
    movement_date: Optional[datetime] = None

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("Количество должно быть положительным")
        return v


class MovementOut(BaseModel):
    id: int
    article_code: str
    article_name: str
    warehouse_name: str
    movement_type: MovementType
    quantity: float
    price_per_unit: Optional[float]
    sales_channel: Optional[SalesChannel]
    comment: Optional[str]
    movement_date: datetime

    model_config = {"from_attributes": True}


# ── Production ────────────────────────────────────────────────────────────────

class ProductionCreate(BaseModel):
    finished_article_code: str
    quantity: float
    comment: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("Количество должно быть положительным")
        return v


class ProductionOut(BaseModel):
    batch_id: int
    finished_article_code: str
    finished_article_name: str
    quantity_produced: float
    components_deducted: List[dict]
    comment: Optional[str]
    produced_at: datetime

    model_config = {"from_attributes": True}


# ── User / Auth ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.OPERATOR


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str]
    role: UserRole
    balance: float
    is_active: bool

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None

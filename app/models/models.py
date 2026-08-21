from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
    Enum, Text, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class ArticleType(str, PyEnum):
    COMPONENT = "component"
    FINISHED = "finished"


class WarehouseType(str, PyEnum):
    COMPONENTS = "components"
    FINISHED_GOODS = "finished_goods"


class MovementType(str, PyEnum):
    RECEIPT = "receipt"        # /po — поступление на склад компонентов
    SHIPMENT = "shipment"      # /ot — отгрузка готовой продукции
    PRODUCTION = "production"  # /pr — производство (списание компонентов + оприходование)
    RETURN = "return"          # возврат от клиента
    WRITE_OFF = "write_off"    # списание / коррекция


class UserRole(str, PyEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class SalesChannel(str, PyEnum):
    MARKETPLACE_1 = "marketplace_1"   # Ozon
    MARKETPLACE_2 = "marketplace_2"   # Яндекс.Маркет
    WEBSITE = "website"               # Собственный сайт
    OTHER = "other"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    warehouse_type = Column(Enum(WarehouseType), nullable=False)

    stock = relationship("Stock", back_populates="warehouse")


class Article(Base):
    """Единый справочник артикулов: и комплектующие (1118-1136), и готовые изделия (FS_*)."""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    article_type = Column(Enum(ArticleType), nullable=False)
    unit = Column(String(20), default="шт")
    cost_price = Column(Float, default=0.0)
    responsible = Column(String(100), nullable=True)
    comment = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="article")
    bom_parent = relationship("BOM", foreign_keys="BOM.parent_id", back_populates="parent")
    bom_child = relationship("BOM", foreign_keys="BOM.child_id", back_populates="child")
    movements = relationship("Movement", back_populates="article")


class BOM(Base):
    """Спецификация: из каких компонентов состоит каждое готовое изделие."""
    __tablename__ = "bom"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("articles.id"), nullable=False)  # готовое изделие
    child_id = Column(Integer, ForeignKey("articles.id"), nullable=False)   # компонент
    quantity = Column(Float, nullable=False, default=1.0)

    __table_args__ = (UniqueConstraint("parent_id", "child_id", name="uq_bom_parent_child"),)

    parent = relationship("Article", foreign_keys=[parent_id], back_populates="bom_parent")
    child = relationship("Article", foreign_keys=[child_id], back_populates="bom_child")


class Stock(Base):
    """Текущий остаток по каждому артикулу на каждом складе."""
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Float, default=0.0)

    __table_args__ = (UniqueConstraint("article_id", "warehouse_id", name="uq_stock_article_warehouse"),)

    article = relationship("Article", back_populates="stock")
    warehouse = relationship("Warehouse", back_populates="stock")


class Movement(Base):
    """
    Журнал всех движений — источник правды для аналитики и отчётов.
    Записи только добавляются, никогда не удаляются.
    """
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=True)
    sales_channel = Column(Enum(SalesChannel), nullable=True)
    comment = Column(Text, nullable=True)
    movement_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    article = relationship("Article", back_populates="movements")
    warehouse = relationship("Warehouse")
    user = relationship("User", back_populates="movements")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    movements = relationship("Movement", back_populates="user")

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
    RECEIPT = "receipt"        # /po
    SHIPMENT = "shipment"      # /ot
    PRODUCTION = "production"  # /pr
    RETURN = "return"
    WRITE_OFF = "write_off"


class UserRole(str, PyEnum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class SalesChannel(str, PyEnum):
    MARKETPLACE_1 = "marketplace_1"
    MARKETPLACE_2 = "marketplace_2"
    WEBSITE = "website"
    OTHER = "other"


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    warehouse_type = Column(Enum(WarehouseType), nullable=False)

    stock = relationship("Stock", back_populates="warehouse")


class Article(Base):
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
    __tablename__ = "bom"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)

    __table_args__ = (UniqueConstraint("parent_id", "child_id", name="uq_bom_parent_child"),)

    parent = relationship("Article", foreign_keys=[parent_id], back_populates="bom_parent")
    child = relationship("Article", foreign_keys=[child_id], back_populates="bom_child")


class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Float, default=0.0)

    __table_args__ = (UniqueConstraint("article_id", "warehouse_id", name="uq_stock_article_warehouse"),)

    article = relationship("Article", back_populates="stock")
    warehouse = relationship("Warehouse", back_populates="stock")


class Movement(Base):
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
    production_batch_id = Column(Integer, ForeignKey("production_batches.id"), nullable=True)

    article = relationship("Article", back_populates="movements")
    warehouse = relationship("Warehouse")
    user = relationship("User", back_populates="movements")
    production_batch = relationship("ProductionBatch", back_populates="movements")


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id = Column(Integer, primary_key=True)
    finished_article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    quantity_produced = Column(Float, nullable=False)
    produced_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(Text, nullable=True)

    movements = relationship("Movement", back_populates="production_batch")
    finished_article = relationship("Article")
    user = relationship("User")


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

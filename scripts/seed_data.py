"""
Импорт начальных данных из warehouse_report.xlsx.

Запуск:
    python scripts/seed_data.py --excel path/to/warehouse_report.xlsx
"""
import argparse
import os
import re
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal, init_db
from app.models.models import (
    Article, ArticleType, BOM, Movement, MovementType,
    Stock, User, UserRole, Warehouse, WarehouseType,
)


def get_or_create_warehouse(db: Session, name: str, wh_type: WarehouseType) -> Warehouse:
    wh = db.query(Warehouse).filter(Warehouse.warehouse_type == wh_type).first()
    if not wh:
        wh = Warehouse(name=name, warehouse_type=wh_type)
        db.add(wh)
        db.flush()
    return wh


def get_or_create_article(db, code, name, art_type, cost=0.0, responsible=None, comment=None):
    a = db.query(Article).filter(Article.code == str(code)).first()
    if not a:
        a = Article(code=str(code), name=name, article_type=art_type,
                    cost_price=cost, responsible=responsible, comment=comment)
        db.add(a)
        db.flush()
    return a


def upsert_stock(db: Session, article_id: int, warehouse_id: int, quantity: float):
    s = db.query(Stock).filter_by(article_id=article_id, warehouse_id=warehouse_id).first()
    if s:
        s.quantity = quantity
    else:
        db.add(Stock(article_id=article_id, warehouse_id=warehouse_id, quantity=quantity))
    db.flush()


def parse_bom_string(bom_str: str) -> list[tuple[str, float]]:
    """'1132 (1), 1118 (1), 1124 (2)' → [('1132', 1.0), ...]"""
    result = []
    for match in re.finditer(r'(\w+)\s*\((\d+(?:\.\d+)?)\)', str(bom_str)):
        result.append((match.group(1), float(match.group(2))))
    return result


def seed(excel_path: str):
    print(f"📂 Читаем файл: {excel_path}")
    wb = openpyxl.load_workbook(excel_path)
    db: Session = SessionLocal()

    try:
        print("\n🏭 Создаём склады...")
        wh_comp = get_or_create_warehouse(db, "Склад компонентов и полуфабрикатов", WarehouseType.COMPONENTS)
        wh_fin = get_or_create_warehouse(db, "Склад готовой продукции", WarehouseType.FINISHED_GOODS)
        db.flush()
        print(f"   ✅ {wh_comp.name}")
        print(f"   ✅ {wh_fin.name}")

        print("\n📦 Импортируем полуфабрикаты...")
        articles_map: dict[str, Article] = {}
        for row in wb["Semi-Finished Products"].iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            code = str(row[0]).strip()
            a = get_or_create_article(
                db, code, str(row[1]).strip(),
                ArticleType.COMPONENT,
                float(row[2] or 0), str(row[3] or ""),
                str(row[4]) if row[4] else None,
            )
            articles_map[code] = a
        db.flush()
        print(f"   ✅ {len(articles_map)} полуфабрикатов")

        print("\n🔧 Импортируем готовые изделия и BOM...")
        finished_map: dict[str, Article] = {}
        for row in wb["Products"].iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            art_code = str(row[0]).strip()
            a = get_or_create_article(db, art_code, str(row[1]).strip(), ArticleType.FINISHED)
            finished_map[art_code] = a
            db.flush()

            db.query(BOM).filter(BOM.parent_id == a.id).delete()
            seen = set()
            for comp_code, qty in parse_bom_string(str(row[2] or "")):
                if comp_code in seen:
                    continue
                seen.add(comp_code)
                comp = articles_map.get(comp_code) or db.query(Article).filter(Article.code == comp_code).first()
                if comp:
                    db.add(BOM(parent_id=a.id, child_id=comp.id, quantity=qty))
                else:
                    print(f"   ⚠️  BOM: компонент '{comp_code}' не найден для {art_code}")
        db.flush()
        print(f"   ✅ {len(finished_map)} готовых изделий")

        print("\n📊 Устанавливаем остатки...")
        count_stock = 0
        for row in wb["Stock"].iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            code, name = str(row[0]).strip(), str(row[1]).strip()
            qty, cost = float(row[2] or 0), float(row[3] or 0)

            a = db.query(Article).filter(Article.code == code).first()
            if not a:
                a = get_or_create_article(db, code, name, ArticleType.COMPONENT, cost)
            a.cost_price = cost / qty if qty > 0 else cost

            wh = wh_fin if a.article_type == ArticleType.FINISHED else wh_comp
            upsert_stock(db, a.id, wh.id, qty)
            count_stock += 1

        for a in list(articles_map.values()) + list(finished_map.values()):
            wh = wh_fin if a.article_type == ArticleType.FINISHED else wh_comp
            if not db.query(Stock).filter_by(article_id=a.id, warehouse_id=wh.id).first():
                db.add(Stock(article_id=a.id, warehouse_id=wh.id, quantity=0))
        db.flush()
        print(f"   ✅ {count_stock} записей остатков")

        print("\n📋 Импортируем историю движений...")
        count_mv, skipped = 0, 0
        for row in wb["Movements"].iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            date_val = row[0]
            name = str(row[1]).strip()
            incoming = float(row[2] or 0)
            outgoing = float(row[3] or 0)
            comment = str(row[4]) if row[4] else None

            mv_date = date_val if isinstance(date_val, datetime) else datetime.utcnow()

            a = db.query(Article).filter(Article.name.ilike(f"%{name}%")).first()
            if not a:
                skipped += 1
                continue

            wh = wh_fin if a.article_type == ArticleType.FINISHED else wh_comp
            if incoming > 0:
                db.add(Movement(article_id=a.id, warehouse_id=wh.id,
                                movement_type=MovementType.RECEIPT,
                                quantity=incoming, comment=comment, movement_date=mv_date))
                count_mv += 1
            if outgoing > 0:
                db.add(Movement(article_id=a.id, warehouse_id=wh.id,
                                movement_type=MovementType.SHIPMENT,
                                quantity=outgoing, comment=comment, movement_date=mv_date))
                count_mv += 1
        db.flush()
        print(f"   ✅ {count_mv} движений импортировано, пропущено: {skipped}")

        print("\n👤 Импортируем пользователей...")
        count_users = 0
        for row in wb["Accounts Balances"].iter_rows(min_row=2, values_only=True):
            if not row[0]:
                continue
            username = str(row[0]).strip()
            role_str = str(row[1] or "user").strip()
            balance = float(row[2] or 0)
            if not db.query(User).filter(User.username == username).first():
                db.add(User(
                    username=username, full_name=username,
                    hashed_password=get_password_hash("changeme123"),
                    role=UserRole.ADMIN if role_str == "admin" else UserRole.OPERATOR,
                    balance=balance,
                ))
                count_users += 1
        db.flush()
        print(f"   ✅ {count_users} пользователей (пароль по умолчанию: changeme123)")

        if not db.query(User).filter(User.username == settings.FIRST_ADMIN_USERNAME).first():
            db.add(User(
                username=settings.FIRST_ADMIN_USERNAME,
                full_name="Администратор",
                hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
            ))
            print(f"\n🔑 Создан admin: {settings.FIRST_ADMIN_USERNAME} / {settings.FIRST_ADMIN_PASSWORD}")

        db.commit()
        print("\n✅ Импорт завершён успешно!")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", default="warehouse_report.xlsx")
    args = parser.parse_args()

    print("🔧 Инициализация БД...")
    init_db()
    print("✅ Таблицы созданы\n")
    seed(args.excel)

from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User, UserRole

# ────────────────────────────────────────────────────────────────────────
# АВТОРИЗАЦИЯ ОТКЛЮЧЕНА (30.07.2026) — по требованию заказчика, для
# упрощения демонстрации (единственный пользователь, не нужно логиниться
# каждый раз и разбираться с "уже зарегистрирован" при повторном seed).
#
# Как это работает сейчас:
#   - auto_error=False → эндпоинты больше НЕ требуют заголовок Authorization.
#   - get_current_user() ИГНОРИРУЕТ токен и всегда возвращает системного
#     администратора, независимо от того, что было передано (или не
#     передано вовсе).
#   - require_admin / require_operator ничего не проверяют — пропускают
#     любого.
#
# Эндпоинт POST /api/auth/login по-прежнему существует и работает
# (в auth.py), просто фронтенд его больше не вызывает.
#
# ЧТОБЫ ВЕРНУТЬ АВТОРИЗАЦИЮ ОБРАТНО — замените тело этого файла на блок
# ниже (это оригинальная версия, до отключения):
#
#   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
#
#   def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
#       credentials_exception = HTTPException(
#           status_code=status.HTTP_401_UNAUTHORIZED,
#           detail="Не удалось проверить учётные данные",
#           headers={"WWW-Authenticate": "Bearer"},
#       )
#       payload = decode_token(token)
#       if payload is None:
#           raise credentials_exception
#       username: str = payload.get("sub")
#       if username is None:
#           raise credentials_exception
#       user = db.query(User).filter(User.username == username).first()
#       if user is None or not user.is_active:
#           raise credentials_exception
#       return user
#
#   def require_admin(current_user: User = Depends(get_current_user)) -> User:
#       if current_user.role != UserRole.ADMIN:
#           raise HTTPException(status_code=403, detail="Требуются права администратора")
#       return current_user
#
#   def require_operator(current_user: User = Depends(get_current_user)) -> User:
#       if current_user.role == UserRole.VIEWER:
#           raise HTTPException(status_code=403, detail="Требуются права оператора или выше")
#       return current_user
#
# (и не забудьте вернуть импорт `from app.core.security import decode_token`
# и `from fastapi import HTTPException, status`)
# ────────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Авторизация отключена: токен не проверяется. Всегда возвращаем
    системного администратора (если он уже был создан seed-скриптом),
    либо временный "виртуальный" объект-заглушку, если БД ещё не заполнена.
    """
    user = db.query(User).filter(User.username == "admin").first()
    if user is None:
        # id=None, а не 0 — чтобы случайно не словить нарушение внешнего
        # ключа при записи движений (movements.user_id допускает NULL).
        user = User(
            id=None,
            username="admin",
            full_name="Системный пользователь (демо-режим)",
            role=UserRole.ADMIN,
            is_active=True,
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def require_operator(current_user: User = Depends(get_current_user)) -> User:
    return current_user

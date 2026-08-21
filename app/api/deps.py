from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.username == "admin").first()
    if user is None:
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
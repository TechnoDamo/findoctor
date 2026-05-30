"""Хеширование и проверка паролей через bcrypt."""

import bcrypt
from app.settings import settings


def hash_password(password: str) -> str:
    """Хеширует пароль для хранения в БД."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хешу."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

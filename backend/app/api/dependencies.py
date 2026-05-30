"""
FastAPI-зависимости: текущий пользователь, соединение с БД.

Каждый защищённый эндпоинт использует `CurrentUser` для получения
аутентифицированного пользователя и `DbConnection` для соединения с БД.
"""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.jwt import decode_access_token
from app.db.pool import get_connection
from app.repositories import auth as auth_repo

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    conn=Depends(get_connection),
) -> dict:
    """
    Извлекает текущего пользователя из JWT access-токена.

    Использует HTTP Bearer-аутентификацию. Токен должен быть действительным
    и содержать `sub` — ID пользователя. Пользователь проверяется в БД.

    Raises:
        HTTPException 401: если токен отсутствует, истёк или недействителен.
    """
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Токен истёк или недействителен")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Некорректный токен")

    session_id = payload.get("sid")
    if session_id is None:
        raise HTTPException(status_code=401, detail="Некорректный токен")

    session = await auth_repo.find_session_by_id(conn, session_id)
    if session is None or str(session["user_id"]) != str(user_id):
        raise HTTPException(status_code=401, detail="Сессия не найдена или отозвана")

    user = await auth_repo.find_user_by_id(conn, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    user["_session_id"] = session_id
    return user


DbConnection = Annotated[get_connection, Depends()]
CurrentUser = Annotated[dict, Depends(get_current_user)]

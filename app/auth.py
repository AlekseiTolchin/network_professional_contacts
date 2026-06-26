import os
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.models import User

load_dotenv()


class RequireLoginException(Exception):
    """Исключение для редиректа на страницу входа."""
    pass

# Контекст хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Секретный ключ для подписания cookie-сессии (из переменной окружения)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY не задана. Проверьте файл .env или переменные окружения.")
serializer = URLSafeSerializer(SECRET_KEY)


def hash_password(password: str) -> str:
    """Хешировать пароль."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Проверить пароль."""
    return pwd_context.verify(plain, hashed)


def create_session_token(user_id: int) -> str:
    """Создать токен сессии."""
    return serializer.dumps({"user_id": user_id})


def get_user_id_from_token(token: str):
    """Извлечь user_id из токена. Вернуть None при ошибке."""
    try:
        data = serializer.loads(token)
        return data.get("user_id")
    except Exception:
        return None


def get_current_user(request: Request, db: Session) -> User | None:
    """Получить текущего пользователя из cookie."""
    token = request.cookies.get("session_token")
    if not token:
        return None
    user_id = get_user_id_from_token(token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_login(request: Request, db: Session) -> User:
    """Проверить авторизацию, иначе — редирект на логин."""
    user = get_current_user(request, db)
    if not user:
        raise RequireLoginException()
    return user


def require_admin(request: Request, db: Session) -> User:
    """Проверить, что пользователь — администратор."""
    user = require_login(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    return user

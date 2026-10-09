from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Configuração do algoritmo Bcrypt para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(senha: str) -> str:
    """Gera o hash seguro bcrypt a partir da senha em texto plano"""
    return pwd_context.hash(senha)


def verify_password(senha_plana: str, senha_hash: str) -> bool:
    """Compara a senha em texto plano com o hash criptografado"""
    return pwd_context.verify(senha_plana, senha_hash)


def create_access_token(sub: str, is_admin: bool, expires_delta: timedelta | None = None) -> str:
    """Gera um token JWT com expiração e claims (sub=email, is_admin)"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": sub,
        "is_admin": is_admin,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida assinatura e expiração do token JWT"""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
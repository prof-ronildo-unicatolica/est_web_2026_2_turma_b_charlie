import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCreate(BaseModel):
    """Payload de registro de novo usuário"""
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=100)


class LoginRequest(BaseModel):
    """Payload de login"""
    email: EmailStr
    senha: str


class Token(BaseModel):
    """Contrato da resposta de login com token JWT"""
    access_token: str
    token_type: str = "bearer"


class UsuarioPublic(BaseModel):
    """Perfil público retornado em /me (nunca expõe o hash da senha)"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    email: str
    is_admin: bool
    ativo: bool
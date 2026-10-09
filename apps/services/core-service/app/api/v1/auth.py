from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, Token, UsuarioCreate, UsuarioPublic
from app.services.auth_service import AuthService, CredenciaisInvalidasError, EmailJaCadastradoError

router = APIRouter(prefix="/auth", tags=["Autenticação & Autorização"])


@router.post(
    "/register",
    response_model=UsuarioPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um novo usuário cliente",
)
def registrar(payload: UsuarioCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        return service.registrar(payload)
    except EmailJaCadastradoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/login",
    response_model=Token,
    summary="Realiza o login e retorna o token JWT",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        access_token = service.autenticar(email=payload.email, senha=payload.senha)
        return Token(access_token=access_token)
    except CredenciaisInvalidasError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get(
    "/me",
    response_model=UsuarioPublic,
    summary="Retorna os dados do usuário logado (requer token JWT)",
)
def get_me(usuario_atual: Usuario = Depends(get_current_user)):
    return usuario_atual


@router.get(
    "/admin/verificacao",
    summary="Valida privilégios administrativos (RBAC - requer is_admin)",
)
def verificacao_admin(admin_atual: Usuario = Depends(get_current_admin)):
    return {
        "status": "ok",
        "mensagem": f"Acesso de administrador concedido para {admin_atual.nome}",
        "admin_id": str(admin_atual.id),
    }
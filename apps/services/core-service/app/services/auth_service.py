from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate


class AuthError(Exception):
    """Base para erros de autenticação."""


class EmailJaCadastradoError(AuthError):
    pass


class CredenciaisInvalidasError(AuthError):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    def registrar(self, payload: UsuarioCreate) -> Usuario:
        email = payload.email.lower().strip()
        if self.repo.get_by_email(email):
            raise EmailJaCadastradoError("Já existe um usuário cadastrado com este e-mail.")

        hash_senha = hash_password(payload.senha)
        return self.repo.create(
            nome=payload.nome.strip(),
            email=email,
            senha_hash=hash_senha,
            is_admin=False,  # Novos registros sempre iniciam como cliente comum
        )

    def autenticar(self, email: str, senha: str) -> str:
        """Autentica o usuário e retorna o token JWT."""
        usuario = self.repo.get_by_email(email.lower().strip())
        if not usuario or not verify_password(senha, usuario.senha_hash):
            raise CredenciaisInvalidasError("E-mail ou senha incorretos.")
        if not usuario.ativo:
            raise CredenciaisInvalidasError("Usuário inativo.")

        return create_access_token(sub=usuario.email, is_admin=usuario.is_admin)


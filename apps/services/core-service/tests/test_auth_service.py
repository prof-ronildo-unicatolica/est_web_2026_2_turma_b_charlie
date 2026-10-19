import pytest
from app.schemas.usuario import UsuarioCreate
from app.services.auth_service import (
    AuthService,
    CredenciaisInvalidasError,
    EmailJaCadastradoError,
)


def test_registrar_usuario_sucesso(db_session):
    service = AuthService(db_session)
    payload = UsuarioCreate(nome="João Teste", email="joao@teste.com", senha="senhaSegura123")
    
    usuario = service.registrar(payload)
    
    assert usuario.id is not None
    assert usuario.email == "joao@teste.com"
    assert usuario.nome == "João Teste"
    assert usuario.is_admin is False
    assert usuario.senha_hash != "senhaSegura123"


def test_registrar_email_duplicado_lanca_excecao(db_session):
    service = AuthService(db_session)
    payload = UsuarioCreate(nome="João", email="duplicado@teste.com", senha="senha123456")
    service.registrar(payload)

    payload_dup = UsuarioCreate(nome="João 2", email="DUPLICADO@teste.com", senha="outrasenha123")
    with pytest.raises(EmailJaCadastradoError) as exc_info:
        service.registrar(payload_dup)
    
    assert "Já existe um usuário cadastrado" in str(exc_info.value)


def test_autenticar_sucesso(db_session):
    service = AuthService(db_session)
    payload = UsuarioCreate(nome="Ana", email="ana@teste.com", senha="minhasenhaforte")
    service.registrar(payload)

    token = service.autenticar("ana@teste.com", "minhasenhaforte")
    
    assert isinstance(token, str)
    assert token.count(".") == 2


def test_autenticar_email_inexistente_lanca_excecao(db_session):
    service = AuthService(db_session)
    with pytest.raises(CredenciaisInvalidasError) as exc_info:
        service.autenticar("naoexiste@teste.com", "senha123")
    
    assert "E-mail ou senha incorretos" in str(exc_info.value)


def test_autenticar_senha_incorreta_lanca_excecao(db_session):
    service = AuthService(db_session)
    payload = UsuarioCreate(nome="Marcos", email="marcos@teste.com", senha="senhaCorreta123")
    service.registrar(payload)

    with pytest.raises(CredenciaisInvalidasError) as exc_info:
        service.autenticar("marcos@teste.com", "senhaErrada999")
    
    assert "E-mail ou senha incorretos" in str(exc_info.value)


def test_autenticar_usuario_inativo_lanca_excecao(db_session):
    service = AuthService(db_session)
    payload = UsuarioCreate(nome="Inativo", email="inativo@teste.com", senha="senha123456")
    usuario = service.registrar(payload)
    
    usuario.ativo = False
    db_session.commit()

    with pytest.raises(CredenciaisInvalidasError) as exc_info:
        service.autenticar("inativo@teste.com", "senha123456")
    
    assert "Usuário inativo" in str(exc_info.value)
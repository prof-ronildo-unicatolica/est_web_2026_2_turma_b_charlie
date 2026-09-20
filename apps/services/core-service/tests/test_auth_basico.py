from app.core.security import create_access_token

BASE = "/api/v1/auth"


def test_registro_usuario_valido(client, db_session):
    payload = {"nome": "Maria Silva", "email": "maria@hotel.com", "senha": "senhaforte123"}
    resp = client.post(f"{BASE}/register", json=payload)
    assert resp.status_code == 201
    dados = resp.json()
    assert dados["email"] == "maria@hotel.com"
    assert "senha" not in dados


def test_registro_email_duplicado_retorna_409(client, db_session):
    payload = {"nome": "Maria", "email": "duplicado@hotel.com", "senha": "123456password"}
    client.post(f"{BASE}/register", json=payload)
    resp2 = client.post(f"{BASE}/register", json=payload)
    assert resp2.status_code == 409


def test_login_retorna_jwt_valido(client, db_session):
    client.post(f"{BASE}/register", json={"nome": "Carlos", "email": "carlos@hotel.com", "senha": "senha123password"})
    resp = client.post(f"{BASE}/login", json={"email": "carlos@hotel.com", "senha": "senha123password"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token.count(".") == 2  # Estrutura padrão de JWT: header.payload.signature


def test_cliente_recebe_403_em_rota_admin(client, db_session):
    token_cliente = create_access_token(sub="cliente@hotel.com", is_admin=False)
    resp = client.get(f"{BASE}/admin/verificacao", headers={"Authorization": f"Bearer {token_cliente}"})
    assert resp.status_code == 403


def test_admin_recebe_200_em_rota_admin(client, db_session):
    token_admin = create_access_token(sub="admin@hotel.com", is_admin=True)
    resp = client.get(f"{BASE}/admin/verificacao", headers={"Authorization": f"Bearer {token_admin}"})
    assert resp.status_code == 200
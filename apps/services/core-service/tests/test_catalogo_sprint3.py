import uuid

from app.core.security import create_access_token, hash_password
from app.repositories.usuario_repository import UsuarioRepository

BASE_ADM = "/api/v1/admin"
BASE_PUB = "/api/v1"


def _garantir_usuario(db_session, email, is_admin):
    repo = UsuarioRepository(db_session)
    if not repo.get_by_email(email):
        repo.create(
            nome="Admin Teste" if is_admin else "Cliente Teste",
            email=email,
            senha_hash=hash_password("senha-de-teste-123"),
            is_admin=is_admin,
        )


def _admin_header(db_session):
    _garantir_usuario(db_session, "admin@hotel.com", is_admin=True)
    token = create_access_token(sub="admin@hotel.com", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


def _cliente_header(db_session):
    _garantir_usuario(db_session, "cliente@hotel.com", is_admin=False)
    token = create_access_token(sub="cliente@hotel.com", is_admin=False)
    return {"Authorization": f"Bearer {token}"}


def _criar_cidade(client, db_session, nome="Cidade Teste"):
    resp = client.post(f"{BASE_ADM}/cidades", json={"nome": nome}, headers=_admin_header(db_session))
    return resp.json()["id"]


def test_cliente_nao_pode_criar_cidade(client, db_session):
    resp = client.post(
        f"{BASE_ADM}/cidades", json={"nome": "Bloqueada"}, headers=_cliente_header(db_session)
    )
    assert resp.status_code == 403


def test_sem_token_nao_pode_criar_cidade(client, db_session):
    resp = client.post(f"{BASE_ADM}/cidades", json={"nome": "Sem Token"})
    assert resp.status_code == 403


def test_admin_cria_cidade(client, db_session):
    resp = client.post(
        f"{BASE_ADM}/cidades", json={"nome": "Brasilia"}, headers=_admin_header(db_session)
    )
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Brasilia"


def test_criar_cidade_com_geojson(client, db_session):
    geojson = {
        "type": "Polygon",
        "coordinates": [[[-47.9, -15.8], [-47.8, -15.8], [-47.8, -15.7], [-47.9, -15.7], [-47.9, -15.8]]],
    }
    resp = client.post(
        f"{BASE_ADM}/cidades",
        json={"nome": "Cidade GeoJSON", "limite_territorial": geojson},
        headers=_admin_header(db_session),
    )
    assert resp.status_code == 201
    assert resp.json()["limite_territorial"]["type"] == "Polygon"


def test_cidade_duplicada_retorna_409(client, db_session):
    payload = {"nome": "Cidade Unica"}
    client.post(f"{BASE_ADM}/cidades", json=payload, headers=_admin_header(db_session))
    resp2 = client.post(f"{BASE_ADM}/cidades", json=payload, headers=_admin_header(db_session))
    assert resp2.status_code == 409


def test_atualizar_cidade(client, db_session):
    cidade_id = _criar_cidade(client, db_session, "Cuiaba Antigo")
    resp = client.put(
        f"{BASE_ADM}/cidades/{cidade_id}",
        json={"nome": "Cuiaba Novo"},
        headers=_admin_header(db_session),
    )
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Cuiaba Novo"


def test_remover_cidade_retorna_204(client, db_session):
    cidade_id = _criar_cidade(client, db_session, "Cidade Para Deletar")
    resp = client.delete(f"{BASE_ADM}/cidades/{cidade_id}", headers=_admin_header(db_session))
    assert resp.status_code == 204


def test_criar_hotel_com_estrelas(client, db_session):
    cidade_id = _criar_cidade(client, db_session, "Sao Paulo")
    resp = client.post(
        f"{BASE_ADM}/hoteis",
        json={"nome": "Grand Hotel SP", "cidade_id": cidade_id, "categoria_estrelas": 5},
        headers=_admin_header(db_session),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["categoria_estrelas"] == 5
    assert data["cidade"]["nome"] == "Sao Paulo"
    assert data["comodidades"] == []


def test_hotel_cidade_inexistente_retorna_404(client, db_session):
    resp = client.post(
        f"{BASE_ADM}/hoteis",
        json={"nome": "Hotel Fantasma", "cidade_id": str(uuid.uuid4())},
        headers=_admin_header(db_session),
    )
    assert resp.status_code == 404


def test_criar_comodidade(client, db_session):
    resp = client.post(
        f"{BASE_ADM}/comodidades", json={"nome": "Piscina"}, headers=_admin_header(db_session)
    )
    assert resp.status_code == 201
    assert resp.json()["nome"] == "Piscina"


def test_comodidade_duplicada_retorna_409(client, db_session):
    payload = {"nome": "Wi-Fi"}
    client.post(f"{BASE_ADM}/comodidades", json=payload, headers=_admin_header(db_session))
    resp2 = client.post(f"{BASE_ADM}/comodidades", json=payload, headers=_admin_header(db_session))
    assert resp2.status_code == 409


def test_associar_comodidade_ao_hotel(client, db_session):
    cidade_id = _criar_cidade(client, db_session, "Rio de Janeiro")
    hotel_id = client.post(
        f"{BASE_ADM}/hoteis",
        json={"nome": "Hotel Rio", "cidade_id": cidade_id},
        headers=_admin_header(db_session),
    ).json()["id"]

    como_id = client.post(
        f"{BASE_ADM}/comodidades", json={"nome": "Sauna"}, headers=_admin_header(db_session)
    ).json()["id"]

    assoc = client.post(
        f"{BASE_ADM}/hoteis/{hotel_id}/comodidades/{como_id}",
        headers=_admin_header(db_session),
    )
    assert assoc.status_code == 200
    nomes = [c["nome"] for c in assoc.json()["comodidades"]]
    assert "Sauna" in nomes


def test_listagem_publica_hoteis_sem_token(client, db_session):
    resp = client.get(f"{BASE_PUB}/hoteis")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_listagem_publica_cidades_sem_token(client, db_session):
    resp = client.get(f"{BASE_PUB}/cidades")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_dod_admin_cadastra_hotel_aparece_na_listagem_publica(client, db_session):
    cidade_id = _criar_cidade(client, db_session, "Porto Velho")
    client.post(
        f"{BASE_ADM}/hoteis",
        json={"nome": "Hotel Madeira", "cidade_id": cidade_id, "categoria_estrelas": 4},
        headers=_admin_header(db_session),
    )
    resp = client.get(f"{BASE_PUB}/hoteis")
    nomes = [h["nome"] for h in resp.json()]
    assert "Hotel Madeira" in nomes

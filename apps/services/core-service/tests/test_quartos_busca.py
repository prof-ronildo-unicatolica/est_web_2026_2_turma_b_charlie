import uuid
import pytest
from app.core.security import create_access_token

BASE_ADM = "/api/v1/admin"
BASE_PUB = "/api/v1"


def _admin_header():
    token = create_access_token(sub="admin@hotel.com", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


def _cliente_header():
    token = create_access_token(sub="cliente@hotel.com", is_admin=False)
    return {"Authorization": f"Bearer {token}"}


def _setup_hotel(client):
    """Cria uma cidade e um hotel para apoiar os testes."""
    cidade_resp = client.post(
        f"{BASE_ADM}/cidades",
        json={"nome": f"Cidade Teste {uuid.uuid4().hex[:6]}"},
        headers=_admin_header(),
    )
    cidade_id = cidade_resp.json()["id"]

    hotel_resp = client.post(
        f"{BASE_ADM}/hoteis",
        json={
            "nome": f"Hotel Teste {uuid.uuid4().hex[:6]}",
            "cidade_id": cidade_id,
            "categoria_estrelas": 4,
        },
        headers=_admin_header(),
    )
    return hotel_resp.json()["id"]



def test_cliente_nao_pode_criar_quarto(client, db_session):
    hotel_id = _setup_hotel(client)
    resp = client.post(
        f"{BASE_ADM}/quartos",
        json={
            "hotel_id": hotel_id,
            "numero": "101",
            "tipo": "Standard",
            "preco_diaria": 150.0,
        },
        headers=_cliente_header(),
    )
    assert resp.status_code == 403


def test_sem_token_nao_pode_listar_quartos_admin(client, db_session):
    resp = client.get(f"{BASE_ADM}/quartos")
    assert resp.status_code == 403



def test_admin_cria_quarto_com_sucesso(client, db_session):
    hotel_id = _setup_hotel(client)
    payload = {
        "hotel_id": hotel_id,
        "numero": "202",
        "tipo": "Casal Luxo",
        "preco_diaria": 320.0,
        "max_adultos": 2,
        "max_criancas": 1,
        "descricao": "Quarto amplo com ar e frigobar",
        "ativo": True,
    }
    resp = client.post(f"{BASE_ADM}/quartos", json=payload, headers=_admin_header())
    assert resp.status_code == 201
    data = resp.json()
    assert data["numero"] == "202"
    assert data["preco_diaria"] == 320.0
    assert data["max_adultos"] == 2
    assert data["max_criancas"] == 1


def test_numero_quarto_duplicado_retorna_409(client, db_session):
    hotel_id = _setup_hotel(client)
    payload = {
        "hotel_id": hotel_id,
        "numero": "301",
        "tipo": "Standard",
        "preco_diaria": 190.0,
    }
    r1 = client.post(f"{BASE_ADM}/quartos", json=payload, headers=_admin_header())
    assert r1.status_code == 201

    r2 = client.post(f"{BASE_ADM}/quartos", json=payload, headers=_admin_header())
    assert r2.status_code == 409


def test_capacidade_invalida_retorna_400(client, db_session):
    hotel_id = _setup_hotel(client)
    payload = {
        "hotel_id": hotel_id,
        "numero": "401",
        "tipo": "Standard",
        "preco_diaria": 190.0,
        "max_adultos": 0,  # Inválido
    }
    resp = client.post(f"{BASE_ADM}/quartos", json=payload, headers=_admin_header())
    assert resp.status_code in [400, 422]


def test_atualizar_quarto(client, db_session):
    hotel_id = _setup_hotel(client)
    q_id = client.post(
        f"{BASE_ADM}/quartos",
        json={"hotel_id": hotel_id, "numero": "501", "tipo": "Standard", "preco_diaria": 200.0},
        headers=_admin_header(),
    ).json()["id"]

    resp = client.put(
        f"{BASE_ADM}/quartos/{q_id}",
        json={"preco_diaria": 250.0, "tipo": "Standard Superior"},
        headers=_admin_header(),
    )
    assert resp.status_code == 200
    assert resp.json()["preco_diaria"] == 250.0
    assert resp.json()["tipo"] == "Standard Superior"


def test_remover_quarto(client, db_session):
    hotel_id = _setup_hotel(client)
    q_id = client.post(
        f"{BASE_ADM}/quartos",
        json={"hotel_id": hotel_id, "numero": "601", "tipo": "Simples", "preco_diaria": 100.0},
        headers=_admin_header(),
    ).json()["id"]

    del_resp = client.delete(f"{BASE_ADM}/quartos/{q_id}", headers=_admin_header())
    assert del_resp.status_code == 204



def test_detalhes_hotel_com_quartos(client, db_session):
    hotel_id = _setup_hotel(client)
    client.post(
        f"{BASE_ADM}/quartos",
        json={"hotel_id": hotel_id, "numero": "701", "tipo": "Suíte Master", "preco_diaria": 500.0, "max_adultos": 3},
        headers=_admin_header(),
    )

    resp = client.get(f"{BASE_PUB}/hoteis/{hotel_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["quartos"]) >= 1
    assert data["quartos"][0]["numero"] == "701"
    assert data["quartos"][0]["max_adultos"] == 3


def test_busca_publica_mongo_retorna_200(client, db_session):
    resp = client.get(f"{BASE_PUB}/busca")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "hoteis" in data
    assert isinstance(data["hoteis"], list)
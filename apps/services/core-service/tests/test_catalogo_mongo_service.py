import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.models.hotel import Cidade, Hotel, Quarto
from app.services.catalogo_mongo_service import CatalogoMongoService



@pytest.fixture
def mock_mongo():
    mock_db = MagicMock()
    mock_col = MagicMock()
    mock_col.create_index = AsyncMock()
    mock_col.replace_one = AsyncMock()
    mock_col.delete_one = AsyncMock()

    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.to_list = AsyncMock(return_value=[{"_id": "hotel_123", "nome": "Hotel Teste"}])
    mock_col.find.return_value = mock_cursor

    mock_db.__getitem__.return_value = mock_col
    return mock_db


def test_inicializar_indices(mock_mongo, db_session):
    """Garante que os índices de busca e o índice espacial 2dsphere são criados."""
    service = CatalogoMongoService(mock_mongo, db_session)
    
    
    asyncio.run(service.inicializar_indices())
    
    assert mock_mongo["catalogo_hoteis"].create_index.call_count >= 5


def test_montar_documento_com_dados_completos(mock_mongo, db_session):
    cidade = Cidade(
        id=uuid.uuid4(),
        nome="Belo Horizonte",
        limite_territorial={"type": "Point", "coordinates": [-43.9, -19.9]},
    )
    hotel = Hotel(
        id=uuid.uuid4(),
        nome="Ouro Minas Palace",
        categoria_estrelas=5,
        cidade=cidade,
    )
    hotel.comodidades = []
    
    quarto_ativo = Quarto(
        id=uuid.uuid4(),
        numero="501",
        tipo="Master",
        preco_diaria=450.0,
        max_adultos=3,
        max_criancas=2,
        ativo=True,
    )
    quarto_inativo = Quarto(
        id=uuid.uuid4(),
        numero="502",
        tipo="Standard",
        preco_diaria=200.0,
        max_adultos=2,
        max_criancas=0,
        ativo=False,  
    )
    hotel.quartos = [quarto_ativo, quarto_inativo]

    service = CatalogoMongoService(mock_mongo, db_session)

    
    doc = service._montar_documento(hotel)

    assert doc["hotel_id"] == str(hotel.id)
    assert doc["nome"] == "Ouro Minas Palace"
    assert doc["preco_minimo"] == 450.0
    assert doc["capacidade_maxima_adultos"] == 3
    assert doc["capacidade_maxima_criancas"] == 2
    assert doc["total_quartos_ativos"] == 1
    assert doc["cidade"]["nome"] == "Belo Horizonte"
    assert doc["cidade"]["limite_territorial"]["type"] == "Point"


def test_montar_documento_sem_quartos_nem_geojson(mock_mongo, db_session):
    cidade = Cidade(id=uuid.uuid4(), nome="Cidade Simples", limite_territorial=None)
    hotel = Hotel(id=uuid.uuid4(), nome="Hotel Novo", categoria_estrelas=None, cidade=cidade)
    hotel.comodidades = []
    hotel.quartos = []

    service = CatalogoMongoService(mock_mongo, db_session)
    doc = service._montar_documento(hotel)

    assert doc["preco_minimo"] == 0.0
    assert doc["capacidade_maxima_adultos"] == 0
    assert doc["capacidade_maxima_criancas"] == 0
    assert doc["total_quartos_ativos"] == 0
    assert doc["cidade"]["limite_territorial"] is None


def test_sincronizar_hotel_inexistente_remove_do_mongo(mock_mongo, db_session):
    service = CatalogoMongoService(mock_mongo, db_session)
    hotel_id = uuid.uuid4()

    doc = asyncio.run(service.sincronizar_hotel(hotel_id))

    assert doc is None
    mock_mongo["catalogo_hoteis"].delete_one.assert_called_once_with({"_id": str(hotel_id)})


def test_sincronizar_hotel_existente_executa_upsert(mock_mongo, db_session):
    cidade = Cidade(id=uuid.uuid4(), nome="Fortaleza")
    db_session.add(cidade)
    db_session.commit()

    hotel = Hotel(id=uuid.uuid4(), nome="Praia Hotel", cidade_id=cidade.id, categoria_estrelas=3)
    db_session.add(hotel)
    db_session.commit()

    service = CatalogoMongoService(mock_mongo, db_session)
    doc = asyncio.run(service.sincronizar_hotel(hotel.id))

    assert doc is not None
    assert doc["nome"] == "Praia Hotel"
    mock_mongo["catalogo_hoteis"].replace_one.assert_called_once()


def test_remover_hotel_do_mongo(mock_mongo, db_session):
    service = CatalogoMongoService(mock_mongo, db_session)
    hotel_id = uuid.uuid4()

    asyncio.run(service.remover_hotel(hotel_id))

    mock_mongo["catalogo_hoteis"].delete_one.assert_called_once_with({"_id": str(hotel_id)})


def test_reconstruir_todo_catalogo(mock_mongo, db_session):
    cidade = Cidade(id=uuid.uuid4(), nome="Sobral")
    db_session.add(cidade)
    db_session.commit()

    h1 = Hotel(id=uuid.uuid4(), nome="Hotel A", cidade_id=cidade.id)
    h2 = Hotel(id=uuid.uuid4(), nome="Hotel B", cidade_id=cidade.id)
    db_session.add_all([h1, h2])
    db_session.commit()

    service = CatalogoMongoService(mock_mongo, db_session)
    total = asyncio.run(service.reconstruir_todo_catalogo())

    assert total >= 2
    assert mock_mongo["catalogo_hoteis"].replace_one.call_count >= 2


def test_buscar_hoteis_com_filtros_e_coordenadas(mock_mongo, db_session):
    service = CatalogoMongoService(mock_mongo, db_session)

    resultados = asyncio.run(
        service.buscar(
            cidade="Fortaleza",
            estrelas=4,
            adultos=2,
            criancas=1,
            preco_max=600.0,
            lat=-3.71,
            lng=-38.54,
        )
    )

    assert len(resultados) == 1
    assert mock_mongo["catalogo_hoteis"].find.called
    

    query_executada = mock_mongo["catalogo_hoteis"].find.call_args[0][0]
    assert "cidade.nome" in query_executada
    assert query_executada["categoria_estrelas"] == {"$gte": 4}
    assert query_executada["preco_minimo"] == {"$lte": 600.0}
    assert "cidade.limite_territorial" in query_executada
    assert "$geoIntersects" in query_executada["cidade.limite_territorial"]

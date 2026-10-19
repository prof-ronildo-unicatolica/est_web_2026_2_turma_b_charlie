import asyncio
import uuid
import pytest

from app.services.hotel_service import (
    CapacidadeInvalidaError,
    CidadeJaExisteError,
    CidadeNaoEncontradaError,
    CidadeService,
    ComodidadeJaExisteError,
    ComodidadeNaoEncontradaError,
    ComodidadeService,
    HotelNaoEncontradoError,
    HotelService,
    QuartoNaoEncontradoError,
    QuartoNumeroDuplicadoError,
    QuartoService,
)


def test_cidade_service_crud_sucesso(db_session):
    service = CidadeService(db_session)
    cidade = service.criar("Salvador", {"type": "Point", "coordinates": [-38.5, -12.9]})
    assert cidade.id is not None
    assert cidade.nome == "Salvador"

    cidade_buscada = service.buscar_por_id(cidade.id)
    assert cidade_buscada.nome == "Salvador"

    atualizada = service.atualizar(cidade.id, {"nome": "Salvador Atualizada"})
    assert atualizada.nome == "Salvador Atualizada"

    service.remover(cidade.id)
    with pytest.raises(CidadeNaoEncontradaError):
        service.buscar_por_id(cidade.id)


def test_cidade_service_duplicidade_lanca_erro(db_session):
    service = CidadeService(db_session)
    service.criar("Recife")
    with pytest.raises(CidadeJaExisteError):
        service.criar(" Recife ")


def test_cidade_service_atualizar_para_nome_existente_lanca_erro(db_session):
    service = CidadeService(db_session)
    c1 = service.criar("Natal")
    c2 = service.criar("Mossoró")
    with pytest.raises(CidadeJaExisteError):
        service.atualizar(c2.id, {"nome": "Natal"})



def test_comodidade_service_crud_sucesso(db_session):
    service = ComodidadeService(db_session)
    com = service.criar("Wi-Fi Grátis")
    assert com.id is not None
    assert com.nome == "Wi-Fi Grátis"

    atualizada = service.atualizar(com.id, "Wi-Fi 5G")
    assert atualizada.nome == "Wi-Fi 5G"

    service.remover(com.id)
    with pytest.raises(ComodidadeNaoEncontradaError):
        service.buscar_por_id(com.id)


def test_comodidade_service_duplicidade_lanca_erro(db_session):
    service = ComodidadeService(db_session)
    service.criar("Piscina Térmica")
    with pytest.raises(ComodidadeJaExisteError):
        service.criar(" Piscina Térmica ")



def test_hotel_service_criar_e_atualizar_sucesso(db_session):
    cid_service = CidadeService(db_session)
    cidade = cid_service.criar("Gramado")

    hotel_service = HotelService(db_session)
    hotel = asyncio.run(hotel_service.criar("Hotel Serra Viva", cidade.id, 5))
    assert hotel.id is not None
    assert hotel.categoria_estrelas == 5

    atualizado = asyncio.run(hotel_service.atualizar(hotel.id, {"nome": "Hotel Serra Viva Premium"}))
    assert atualizado.nome == "Hotel Serra Viva Premium"


def test_hotel_service_criar_cidade_invalida_lanca_erro(db_session):
    hotel_service = HotelService(db_session)
    with pytest.raises(CidadeNaoEncontradaError):
        asyncio.run(hotel_service.criar("Hotel Fantasma", uuid.uuid4()))


def test_hotel_service_associar_comodidade(db_session):
    cid_service = CidadeService(db_session)
    cidade = cid_service.criar("Canela")
    com_service = ComodidadeService(db_session)
    comodidade = com_service.criar("Lareira")

    hotel_service = HotelService(db_session)
    hotel = asyncio.run(hotel_service.criar("Pousada Encantada", cidade.id, 4))

    h_com = asyncio.run(hotel_service.adicionar_comodidade(hotel.id, comodidade.id))
    assert any(c.nome == "Lareira" for c in h_com.comodidades)

    h_sem = asyncio.run(hotel_service.remover_comodidade(hotel.id, comodidade.id))
    assert not any(c.nome == "Lareira" for c in h_sem.comodidades)



def test_quarto_service_criar_sucesso(db_session):
    cid = CidadeService(db_session).criar("Maceió")
    hotel = asyncio.run(HotelService(db_session).criar("Maceió Flat", cid.id, 4))

    quarto_service = QuartoService(db_session)
    quarto = asyncio.run(
        quarto_service.criar(
            hotel_id=hotel.id,
            numero="201",
            tipo="Deluxe",
            preco_diaria=250.0,
            max_adultos=2,
            max_criancas=1,
        )
    )
    assert quarto.id is not None
    assert quarto.numero == "201"
    assert quarto.preco_diaria == 250.0


def test_quarto_service_numero_duplicado_lanca_erro(db_session):
    cid = CidadeService(db_session).criar("Aracaju")
    hotel = asyncio.run(HotelService(db_session).criar("Aracaju Suítes", cid.id, 3))

    quarto_service = QuartoService(db_session)
    asyncio.run(quarto_service.criar(hotel.id, "101", "Standard", 150.0))

    with pytest.raises(QuartoNumeroDuplicadoError):
        asyncio.run(quarto_service.criar(hotel.id, "101", "Standard Duplo", 180.0))


def test_quarto_service_capacidades_invalidas_lanca_erro(db_session):
    cid = CidadeService(db_session).criar("Curitiba")
    hotel = asyncio.run(HotelService(db_session).criar("Curitiba Hotel", cid.id, 3))
    quarto_service = QuartoService(db_session)

    # Adultos < 1
    with pytest.raises(CapacidadeInvalidaError):
        asyncio.run(quarto_service.criar(hotel.id, "102", "Standard", 150.0, max_adultos=0))

    # Crianças < 0
    with pytest.raises(CapacidadeInvalidaError):
        asyncio.run(quarto_service.criar(hotel.id, "103", "Standard", 150.0, max_criancas=-1))
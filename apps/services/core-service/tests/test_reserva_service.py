import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models.hotel import Cidade, Hotel, Quarto
from app.schemas.pricing import (
    CotacaoRequestSchema,
    ServicoAdicionalCreateSchema,
    ServicoAdicionalUpdateSchema,
    TarifaTemporadaCreateSchema,
    TarifaTemporadaUpdateSchema,
)
from app.services.reserva_service import (
    CapacidadeExcedidaError,
    DatasInvalidasError,
    RecursoNaoEncontradoError,
    ReservaService,
)


@pytest.fixture
def cenario(db_session):
    cidade = Cidade(id=uuid.uuid4(), nome="Fortaleza")
    hotel = Hotel(
        id=uuid.uuid4(),
        nome="Hotel Teste",
        cidade_id=cidade.id,
        categoria_estrelas=4,
    )
    quarto = Quarto(
        id=uuid.uuid4(),
        hotel_id=hotel.id,
        numero="101",
        tipo="Standard",
        preco_diaria=200.0,
        max_adultos=2,
        max_criancas=2,
        ativo=True,
    )
    db_session.add_all([cidade, hotel, quarto])
    db_session.commit()
    return ReservaService(db_session), quarto


def pedido(quarto, **alteracoes):
    dados = {
        "quarto_id": quarto.id,
        "checkin": date(2026, 10, 1),
        "checkout": date(2026, 10, 4),
        "adultos": 2,
    }
    dados.update(alteracoes)
    return CotacaoRequestSchema(**dados)


def criar_tarifa(service, quarto, **alteracoes):
    dados = {
        "hotel_id": quarto.hotel_id,
        "nome": "Temporada",
        "data_inicio": date(2026, 10, 1),
        "data_fim": date(2026, 10, 4),
        "multiplicador": 1.5,
    }
    dados.update(alteracoes)
    return service.criar_tarifa_temporada(
        TarifaTemporadaCreateSchema(**dados)
    )


def criar_adicional(service, quarto, **alteracoes):
    dados = {
        "hotel_id": quarto.hotel_id,
        "nome": "Cafe da manha",
        "preco": 30.0,
        "por_diaria": True,
    }
    dados.update(alteracoes)
    return service.criar_servico_adicional(
        ServicoAdicionalCreateSchema(**dados)
    )


def test_estadia_simples(cenario):
    service, quarto = cenario
    resultado = service.calcular_cotacao(pedido(quarto))

    assert resultado.num_diarias == 3
    assert len(resultado.diarias) == 3
    assert resultado.diarias[-1].data == date(2026, 10, 3)
    assert resultado.subtotal_diarias == 600.0
    assert resultado.adicional_criancas == 0.0
    assert resultado.valor_bebes == 0.0
    assert resultado.taxa_early_checkin == 0.0
    assert resultado.taxa_late_checkout == 0.0
    assert resultado.desconto_nao_reembolsavel == 0.0
    assert resultado.total_servicos_adicionais == 0.0
    assert resultado.valor_total == 600.0


def test_criancas_50_porcento_e_bebes_gratis(cenario):
    service, quarto = cenario
    resultado = service.calcular_cotacao(
        pedido(quarto, criancas=1, bebes=1)
    )

    assert resultado.adicional_criancas == 300.0
    assert resultado.valor_bebes == 0.0
    assert resultado.valor_total == 900.0


def test_temporada_aplicada_somente_nas_datas_corretas(cenario):
    service, quarto = cenario
    criar_tarifa(
        service,
        quarto,
        data_inicio=date(2026, 10, 2),
        data_fim=date(2026, 10, 3),
    )
    resultado = service.calcular_cotacao(pedido(quarto))

    assert [d.valor_final for d in resultado.diarias] == [
        200.0, 300.0, 300.0
    ]
    assert resultado.valor_total == 800.0


def test_temporada_com_multiplicador_menor_que_um(cenario):
    service, quarto = cenario
    criar_tarifa(service, quarto, multiplicador=0.8)
    resultado = service.calcular_cotacao(pedido(quarto))

    assert all(d.valor_final == 160.0 for d in resultado.diarias)
    assert resultado.valor_total == 480.0


def test_temporadas_sobrepostas_usam_maior_multiplicador(cenario):
    service, quarto = cenario
    criar_tarifa(service, quarto, nome="Baixa", multiplicador=0.8)
    criar_tarifa(service, quarto, nome="Outra", multiplicador=0.9)
    resultado = service.calcular_cotacao(pedido(quarto))

    assert all(
        d.multiplicador_temporada == 0.9 for d in resultado.diarias
    )
    assert resultado.valor_total == 540.0


def test_temporada_inativa_nao_altera_preco(cenario):
    service, quarto = cenario
    criar_tarifa(service, quarto, ativo=False)
    resultado = service.calcular_cotacao(pedido(quarto))

    assert resultado.valor_total == 600.0


@pytest.mark.parametrize(
    "early,late,total",
    [
        (True, False, 460.0),
        (False, True, 460.0),
        (True, True, 520.0),
    ],
)
def test_early_checkin_e_late_checkout(cenario, early, late, total):
    service, quarto = cenario
    resultado = service.calcular_cotacao(
        pedido(
            quarto,
            checkout=date(2026, 10, 3),
            early_checkin=early,
            late_checkout=late,
        )
    )

    assert resultado.taxa_early_checkin == (60.0 if early else 0.0)
    assert resultado.taxa_late_checkout == (60.0 if late else 0.0)
    assert resultado.valor_total == total


def test_desconto_nao_reembolsavel(cenario):
    service, quarto = cenario
    resultado = service.calcular_cotacao(
        pedido(quarto, tipo_tarifa="nao_reembolsavel")
    )

    assert resultado.desconto_nao_reembolsavel == 60.0
    assert resultado.valor_total == 540.0


def test_servicos_por_diaria_e_taxa_fixa(cenario):
    service, quarto = cenario
    diario = criar_adicional(service, quarto)
    fixo = criar_adicional(
        service, quarto, nome="Translado", preco=80.0, por_diaria=False
    )
    resultado = service.calcular_cotacao(
        pedido(quarto, servicos_adicionais_ids=[diario.id, fixo.id])
    )

    assert len(resultado.servicos_selecionados) == 2
    assert resultado.total_servicos_adicionais == 170.0
    assert resultado.valor_total == 770.0


def test_cenario_completo_e_invariancia_do_breakdown(cenario):
    service, quarto = cenario
    criar_tarifa(service, quarto, multiplicador=1.2)
    adicional = criar_adicional(service, quarto, preco=25.0)
    requisicao = pedido(
        quarto,
        checkout=date(2026, 10, 3),
        criancas=1,
        bebes=1,
        early_checkin=True,
        late_checkout=True,
        tipo_tarifa="nao_reembolsavel",
        servicos_adicionais_ids=[adicional.id],
    )
    resultado = service.calcular_cotacao(requisicao)

    assert resultado.subtotal_diarias == 480.0
    assert resultado.adicional_criancas == 200.0
    assert resultado.subtotal_estadia == 800.0
    assert resultado.desconto_nao_reembolsavel == 80.0
    assert resultado.total_servicos_adicionais == 50.0
    assert resultado.valor_total == 770.0

    total_breakdown = (
        Decimal(str(resultado.subtotal_diarias))
        + Decimal(str(resultado.adicional_criancas))
        + Decimal(str(resultado.valor_bebes))
        + Decimal(str(resultado.taxa_early_checkin))
        + Decimal(str(resultado.taxa_late_checkout))
        - Decimal(str(resultado.desconto_nao_reembolsavel))
        + Decimal(str(resultado.total_servicos_adicionais))
    )
    assert Decimal(str(resultado.valor_total)) == total_breakdown
    assert (
        service.calcular_cotacao(requisicao).model_dump()
        == resultado.model_dump()
    )


@pytest.mark.parametrize("checkout", [date(2026, 10, 1), date(2026, 9, 30)])
def test_datas_invalidas(cenario, checkout):
    service, quarto = cenario

    with pytest.raises(DatasInvalidasError):
        service.calcular_cotacao(pedido(quarto, checkout=checkout))


@pytest.mark.parametrize(
    "alteracoes", [{"adultos": 3}, {"criancas": 3}]
)
def test_capacidade_excedida(cenario, alteracoes):
    service, quarto = cenario

    with pytest.raises(CapacidadeExcedidaError):
        service.calcular_cotacao(pedido(quarto, **alteracoes))


def test_quarto_inexistente(cenario):
    service, quarto = cenario

    with pytest.raises(RecursoNaoEncontradoError):
        service.calcular_cotacao(
            pedido(quarto, quarto_id=uuid.uuid4())
        )


def test_quarto_inativo(cenario):
    service, quarto = cenario
    quarto.ativo = False
    service.db.commit()

    with pytest.raises(RecursoNaoEncontradoError):
        service.calcular_cotacao(pedido(quarto))


def test_servico_inexistente_rejeitado(cenario):
    service, quarto = cenario

    with pytest.raises(RecursoNaoEncontradoError):
        service.calcular_cotacao(
            pedido(quarto, servicos_adicionais_ids=[uuid.uuid4()])
        )


def test_servico_inativo_rejeitado(cenario):
    service, quarto = cenario
    adicional = criar_adicional(service, quarto, ativo=False)

    with pytest.raises(RecursoNaoEncontradoError):
        service.calcular_cotacao(
            pedido(quarto, servicos_adicionais_ids=[adicional.id])
        )


def test_servico_de_outro_hotel_rejeitado(cenario):
    service, quarto = cenario
    outro_hotel = Hotel(
        id=uuid.uuid4(),
        nome="Outro Hotel",
        cidade_id=quarto.hotel.cidade_id,
    )
    service.db.add(outro_hotel)
    service.db.commit()
    adicional = criar_adicional(
        service, quarto, hotel_id=outro_hotel.id
    )

    with pytest.raises(RecursoNaoEncontradoError):
        service.calcular_cotacao(
            pedido(quarto, servicos_adicionais_ids=[adicional.id])
        )


def test_crud_tarifa_temporada(cenario):
    service, quarto = cenario
    tarifa = criar_tarifa(service, quarto)
    tarifa_id = tarifa.id

    assert service.obter_tarifa_temporada(tarifa_id).nome == "Temporada"
    assert len(service.listar_tarifas_temporada(quarto.hotel_id)) == 1

    atualizada = service.atualizar_tarifa_temporada(
        tarifa_id,
        TarifaTemporadaUpdateSchema(
            nome="Baixa",
            multiplicador=0.8,
            ativo=False,
            data_inicio=date(2026, 10, 2),
            data_fim=date(2026, 10, 5),
        ),
    )

    assert atualizada.nome == "Baixa"
    assert atualizada.multiplicador == 0.8
    assert atualizada.ativo is False
    assert service.listar_tarifas_temporada(
        quarto.hotel_id, apenas_ativas=True
    ) == []
    assert len(service.listar_tarifas_temporada(quarto.hotel_id)) == 1

    service.remover_tarifa_temporada(tarifa_id)

    with pytest.raises(RecursoNaoEncontradoError):
        service.obter_tarifa_temporada(tarifa_id)


def test_criacao_tarifa_com_datas_invalidas(cenario):
    service, quarto = cenario

    with pytest.raises(DatasInvalidasError):
        criar_tarifa(
            service, quarto, data_fim=date(2026, 10, 1)
        )


def test_atualizacao_tarifa_com_datas_invalidas(cenario):
    service, quarto = cenario
    tarifa = criar_tarifa(service, quarto)

    with pytest.raises(DatasInvalidasError):
        service.atualizar_tarifa_temporada(
            tarifa.id,
            TarifaTemporadaUpdateSchema(
                data_fim=date(2026, 10, 1)
            ),
        )


def test_crud_servico_adicional(cenario):
    service, quarto = cenario
    adicional = criar_adicional(service, quarto)
    adicional_id = adicional.id

    assert service.obter_servico_adicional(adicional_id).preco == 30.0
    assert len(service.listar_servicos_adicionais(quarto.hotel_id)) == 1

    atualizado = service.atualizar_servico_adicional(
        adicional_id,
        ServicoAdicionalUpdateSchema(
            nome="Servico atualizado",
            descricao="Nova descricao",
            preco=0.0,
            por_diaria=False,
            ativo=False,
        ),
    )

    assert atualizado.nome == "Servico atualizado"
    assert atualizado.descricao == "Nova descricao"
    assert atualizado.preco == 0.0
    assert atualizado.por_diaria is False
    assert atualizado.ativo is False
    assert service.listar_servicos_adicionais(
        quarto.hotel_id, apenas_ativos=True
    ) == []
    assert len(service.listar_servicos_adicionais(quarto.hotel_id)) == 1

    service.remover_servico_adicional(adicional_id)

    with pytest.raises(RecursoNaoEncontradoError):
        service.obter_servico_adicional(adicional_id)

@pytest.mark.parametrize(
    "preco,taxa,total",
    [
        (8.95, 2.69, 14.33),
        (8.85, 2.66, 14.17),
    ],
)
def test_arredondamento_decimal_early_e_late(cenario, preco, taxa, total):
    service, quarto = cenario
    quarto.preco_diaria = preco
    service.db.commit()

    resultado = service.calcular_cotacao(
        pedido(
            quarto,
            checkout=date(2026, 10, 2),
            early_checkin=True,
            late_checkout=True,
        )
    )

    assert resultado.taxa_early_checkin == taxa
    assert resultado.taxa_late_checkout == taxa
    assert resultado.valor_total == total


def test_arredondamento_decimal_crianca(cenario):
    service, quarto = cenario
    quarto.preco_diaria = 19.99
    service.db.commit()

    resultado = service.calcular_cotacao(
        pedido(quarto, checkout=date(2026, 10, 2), criancas=1)
    )

    assert resultado.adicional_criancas == 10.0
    assert resultado.valor_total == 29.99


def test_arredondamento_decimal_desconto(cenario):
    service, quarto = cenario
    quarto.preco_diaria = 10.05
    service.db.commit()

    resultado = service.calcular_cotacao(
        pedido(
            quarto,
            checkout=date(2026, 10, 2),
            tipo_tarifa="nao_reembolsavel",
        )
    )

    assert resultado.desconto_nao_reembolsavel == 1.01
    assert resultado.valor_total == 9.04


def test_arredondamento_decimal_temporada(cenario):
    service, quarto = cenario
    quarto.preco_diaria = 1.07
    service.db.commit()
    criar_tarifa(service, quarto, multiplicador=2.5)

    resultado = service.calcular_cotacao(
        pedido(quarto, checkout=date(2026, 10, 2))
    )

    assert resultado.diarias[0].valor_final == 2.68
    assert resultado.valor_total == 2.68
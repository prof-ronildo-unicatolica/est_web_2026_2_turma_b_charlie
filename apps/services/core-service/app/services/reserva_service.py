import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.hotel import Quarto, ServicoAdicional, TarifaTemporada
from app.repositories.hotel_repository import QuartoRepository
from app.repositories.pricing_repository import (
    ServicoAdicionalRepository,
    TarifaTemporadaRepository,
)
from app.schemas.pricing import (
    CotacaoRequestSchema,
    CotacaoResponseSchema,
    DetalheDiariaSchema,
    ItemServicoCalculadoSchema,
    ServicoAdicionalCreateSchema,
    ServicoAdicionalUpdateSchema,
    TarifaTemporadaCreateSchema,
    TarifaTemporadaUpdateSchema,
)


class ReservaServiceError(Exception):
    """Exceção base de serviço de reservas e precificação."""


class DatasInvalidasError(ReservaServiceError):
    pass


class CapacidadeExcedidaError(ReservaServiceError):
    pass


class RecursoNaoEncontradoError(ReservaServiceError):
    pass


class ReservaService:
    def __init__(self, db: Session):
        self.db = db
        self.quarto_repo = QuartoRepository(db)
        self.tarifa_repo = TarifaTemporadaRepository(db)
        self.servico_repo = ServicoAdicionalRepository(db)

    def criar_tarifa_temporada(self, payload: TarifaTemporadaCreateSchema) -> TarifaTemporada:
        if payload.data_fim <= payload.data_inicio:
            raise DatasInvalidasError("A data final da tarifa deve ser posterior à data inicial.")
        return self.tarifa_repo.create(
            hotel_id=payload.hotel_id,
            nome=payload.nome,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
            multiplicador=payload.multiplicador,
            ativo=payload.ativo,
        )

    def listar_tarifas_temporada(self, hotel_id: uuid.UUID, apenas_ativas: bool = False) -> List[TarifaTemporada]:
        return self.tarifa_repo.list_by_hotel(hotel_id, apenas_ativas=apenas_ativas)

    def obter_tarifa_temporada(self, tarifa_id: uuid.UUID) -> TarifaTemporada:
        tarifa = self.tarifa_repo.get_by_id(tarifa_id)
        if not tarifa:
            raise RecursoNaoEncontradoError("Tarifa de temporada não encontrada.")
        return tarifa

    def atualizar_tarifa_temporada(self, tarifa_id: uuid.UUID, payload: TarifaTemporadaUpdateSchema) -> TarifaTemporada:
        tarifa = self.obter_tarifa_temporada(tarifa_id)
        data_ini = payload.data_inicio or tarifa.data_inicio
        data_fim = payload.data_fim or tarifa.data_fim
        if data_fim <= data_ini:
            raise DatasInvalidasError("A data final da tarifa deve ser posterior à data inicial.")
        return self.tarifa_repo.update(tarifa, **payload.model_dump(exclude_unset=True))

    def remover_tarifa_temporada(self, tarifa_id: uuid.UUID) -> None:
        tarifa = self.obter_tarifa_temporada(tarifa_id)
        self.tarifa_repo.delete(tarifa)

    def criar_servico_adicional(self, payload: ServicoAdicionalCreateSchema) -> ServicoAdicional:
        return self.servico_repo.create(
            hotel_id=payload.hotel_id,
            nome=payload.nome,
            preco=payload.preco,
            por_diaria=payload.por_diaria,
            descricao=payload.descricao,
            ativo=payload.ativo,
        )

    def listar_servicos_adicionais(self, hotel_id: uuid.UUID, apenas_ativos: bool = False) -> List[ServicoAdicional]:
        return self.servico_repo.list_by_hotel(hotel_id, apenas_ativos=apenas_ativos)

    def obter_servico_adicional(self, servico_id: uuid.UUID) -> ServicoAdicional:
        servico = self.servico_repo.get_by_id(servico_id)
        if not servico:
            raise RecursoNaoEncontradoError("Serviço adicional não encontrado.")
        return servico

    def atualizar_servico_adicional(self, servico_id: uuid.UUID, payload: ServicoAdicionalUpdateSchema) -> ServicoAdicional:
        servico = self.obter_servico_adicional(servico_id)
        return self.servico_repo.update(servico, **payload.model_dump(exclude_unset=True))

    def remover_servico_adicional(self, servico_id: uuid.UUID) -> None:
        servico = self.obter_servico_adicional(servico_id)
        self.servico_repo.delete(servico)

    def calcular_cotacao(self, req: CotacaoRequestSchema) -> CotacaoResponseSchema:
        centavo = Decimal("0.01")
        zero = Decimal("0.00")

        def arredondar(valor):
            return valor.quantize(centavo, rounding=ROUND_HALF_UP)

        if req.checkout <= req.checkin:
            raise DatasInvalidasError(
                "Data de checkout deve ser posterior à data de checkin."
            )

        quarto = self.quarto_repo.get_by_id(req.quarto_id)
        if not quarto or not quarto.ativo:
            raise RecursoNaoEncontradoError(
                "Quarto não encontrado ou inativo."
            )

        if req.adultos > quarto.max_adultos:
            raise CapacidadeExcedidaError(
                f"Quarto suporta no máximo {quarto.max_adultos} adulto(s). "
                f"Solicitado: {req.adultos}."
            )

        if req.criancas > quarto.max_criancas:
            raise CapacidadeExcedidaError(
                f"Quarto suporta no máximo {quarto.max_criancas} criança(s). "
                f"Solicitado: {req.criancas}."
            )

        num_diarias = (req.checkout - req.checkin).days
        preco_base = Decimal(str(quarto.preco_diaria))

        tarifas = self.tarifa_repo.list_by_hotel(
            quarto.hotel_id, apenas_ativas=True
        )

        detalhe_diarias = []
        subtotal_diarias = zero
        data_atual = req.checkin

        while data_atual < req.checkout:
            multiplicador = Decimal("1")
            tarifa_nome = None

            for tarifa in tarifas:
                if tarifa.data_inicio <= data_atual <= tarifa.data_fim:
                    candidato = Decimal(str(tarifa.multiplicador))
                    if tarifa_nome is None or candidato > multiplicador:
                        multiplicador = candidato
                        tarifa_nome = tarifa.nome

            valor_dia = arredondar(preco_base * multiplicador)
            subtotal_diarias += valor_dia

            detalhe_diarias.append(
                DetalheDiariaSchema(
                    data=data_atual,
                    preco_base=float(preco_base),
                    multiplicador_temporada=float(multiplicador),
                    valor_final=float(valor_dia),
                    tarifa_aplicada=tarifa_nome,
                )
            )

            data_atual += timedelta(days=1)

        subtotal_diarias = arredondar(subtotal_diarias)

        adicional_criancas = arredondar(
            Decimal(req.criancas)
            * Decimal("0.50")
            * preco_base
            * num_diarias
        )

        taxa_early = (
            arredondar(Decimal("0.30") * preco_base)
            if req.early_checkin
            else zero
        )

        taxa_late = (
            arredondar(Decimal("0.30") * preco_base)
            if req.late_checkout
            else zero
        )

        subtotal_estadia = arredondar(
            subtotal_diarias + adicional_criancas + taxa_early + taxa_late
        )

        desconto_nao_reembolsavel = zero
        if req.tipo_tarifa == "nao_reembolsavel":
            desconto_nao_reembolsavel = arredondar(
                subtotal_estadia * Decimal("0.10")
            )

        servicos_calculados = []
        total_servicos = zero

        if req.servicos_adicionais_ids:
            servicos_db = self.servico_repo.list_by_ids(
                req.servicos_adicionais_ids
            )

            ids_solicitados = set(req.servicos_adicionais_ids)
            ids_validos = {
                servico.id
                for servico in servicos_db
                if servico.hotel_id == quarto.hotel_id
            }

            if ids_solicitados != ids_validos:
                raise RecursoNaoEncontradoError(
                    "Um ou mais serviços não existem, estão inativos "
                    "ou não pertencem ao hotel do quarto."
                )

            for servico in servicos_db:
                dias = num_diarias if servico.por_diaria else 1
                preco_servico = Decimal(str(servico.preco))
                custo_servico = arredondar(preco_servico * dias)
                total_servicos += custo_servico

                servicos_calculados.append(
                    ItemServicoCalculadoSchema(
                        id=servico.id,
                        nome=servico.nome,
                        preco_unitario=float(preco_servico),
                        por_diaria=servico.por_diaria,
                        quantidade_dias=dias,
                        valor_total=float(custo_servico),
                    )
                )

        total_servicos = arredondar(total_servicos)

        valor_total = arredondar(
            subtotal_estadia - desconto_nao_reembolsavel + total_servicos
        )

        return CotacaoResponseSchema(
            quarto_id=quarto.id,
            quarto_tipo=quarto.tipo,
            quarto_numero=quarto.numero,
            preco_base_diaria=float(preco_base),
            checkin=req.checkin,
            checkout=req.checkout,
            num_diarias=num_diarias,
            adultos=req.adultos,
            criancas=req.criancas,
            bebes=req.bebes,
            diarias=detalhe_diarias,
            subtotal_diarias=float(subtotal_diarias),
            adicional_criancas=float(adicional_criancas),
            valor_bebes=float(zero),
            taxa_early_checkin=float(taxa_early),
            taxa_late_checkout=float(taxa_late),
            subtotal_estadia=float(subtotal_estadia),
            desconto_nao_reembolsavel=float(desconto_nao_reembolsavel),
            servicos_selecionados=servicos_calculados,
            total_servicos_adicionais=float(total_servicos),
            valor_total=float(valor_total),
        )
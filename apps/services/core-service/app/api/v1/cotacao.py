import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.pricing import (
    CotacaoRequestSchema,
    CotacaoResponseSchema,
    ServicoAdicionalCreateSchema,
    ServicoAdicionalResponseSchema,
    ServicoAdicionalUpdateSchema,
    TarifaTemporadaCreateSchema,
    TarifaTemporadaResponseSchema,
    TarifaTemporadaUpdateSchema,
)
from app.services.reserva_service import (
    CapacidadeExcedidaError,
    DatasInvalidasError,
    RecursoNaoEncontradoError,
    ReservaService,
)

router = APIRouter(tags=["Precificação & Reservas (Sprint 5)"])


# Cotação pública
@router.post(
    "/cotacao",
    response_model=CotacaoResponseSchema,
    summary="Calcula cotação com breakdown financeiro completo",
)
def calcular_cotacao(
    payload: CotacaoRequestSchema,
    db: Session = Depends(get_db),
):
    service = ReservaService(db)
    try:
        return service.calcular_cotacao(payload)
    except DatasInvalidasError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except CapacidadeExcedidaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except RecursoNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# Listagem pública de serviços ativos
@router.get(
    "/servicos-adicionais",
    response_model=List[ServicoAdicionalResponseSchema],
    summary="Lista serviços adicionais ativos de um hotel",
)
def listar_servicos_publicos(
    hotel_id: uuid.UUID = Query(..., description="ID do hotel"),
    db: Session = Depends(get_db),
):
    service = ReservaService(db)
    return service.listar_servicos_adicionais(
        hotel_id, apenas_ativos=True
    )


# CRUD administrativo de tarifas de temporada
@router.post(
    "/admin/tarifas-temporada",
    response_model=TarifaTemporadaResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Cria uma tarifa de temporada",
)
def criar_tarifa_temporada(
    payload: TarifaTemporadaCreateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    try:
        return service.criar_tarifa_temporada(payload)
    except DatasInvalidasError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/admin/tarifas-temporada",
    response_model=List[TarifaTemporadaResponseSchema],
    summary="[ADMIN] Lista tarifas de temporada de um hotel",
)
def listar_tarifas_temporada(
    hotel_id: uuid.UUID = Query(..., description="ID do hotel"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    return service.listar_tarifas_temporada(
        hotel_id, apenas_ativas=False
    )


@router.put(
    "/admin/tarifas-temporada/{tarifa_id}",
    response_model=TarifaTemporadaResponseSchema,
    summary="[ADMIN] Atualiza uma tarifa de temporada",
)
def atualizar_tarifa_temporada(
    tarifa_id: uuid.UUID,
    payload: TarifaTemporadaUpdateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    try:
        return service.atualizar_tarifa_temporada(
            tarifa_id, payload
        )
    except RecursoNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DatasInvalidasError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete(
    "/admin/tarifas-temporada/{tarifa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove uma tarifa de temporada",
)
def remover_tarifa_temporada(
    tarifa_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    try:
        service.remover_tarifa_temporada(tarifa_id)
    except RecursoNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# CRUD administrativo de serviços adicionais
@router.post(
    "/admin/servicos-adicionais",
    response_model=ServicoAdicionalResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Cria um serviço adicional",
)
def criar_servico_adicional(
    payload: ServicoAdicionalCreateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    return service.criar_servico_adicional(payload)


@router.get(
    "/admin/servicos-adicionais",
    response_model=List[ServicoAdicionalResponseSchema],
    summary="[ADMIN] Lista todos os serviços adicionais de um hotel",
)
def listar_servicos_admin(
    hotel_id: uuid.UUID = Query(..., description="ID do hotel"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    return service.listar_servicos_adicionais(
        hotel_id, apenas_ativos=False
    )


@router.put(
    "/admin/servicos-adicionais/{servico_id}",
    response_model=ServicoAdicionalResponseSchema,
    summary="[ADMIN] Atualiza um serviço adicional",
)
def atualizar_servico_adicional(
    servico_id: uuid.UUID,
    payload: ServicoAdicionalUpdateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    try:
        return service.atualizar_servico_adicional(
            servico_id, payload
        )
    except RecursoNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


@router.delete(
    "/admin/servicos-adicionais/{servico_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove um serviço adicional",
)
def remover_servico_adicional(
    servico_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ReservaService(db)
    try:
        service.remover_servico_adicional(servico_id)
    except RecursoNaoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
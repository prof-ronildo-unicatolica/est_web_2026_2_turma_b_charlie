import uuid
from typing import List

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db, get_mongo_db
from app.models.usuario import Usuario
from app.repositories.avaliacao_repository import AvaliacaoRepository
from app.schemas.avaliacao import (
    AvaliacaoCreateSchema,
    AvaliacaoResponseSchema,
    HotelMediaAvaliacoesSchema,
)
from app.services.avaliacao_service import AvaliacaoService

router = APIRouter(prefix="/avaliacoes", tags=["Avaliações de Estadias"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=AvaliacaoResponseSchema,
    summary="Registra avaliação de uma estadia concluída",
)
async def criar_avaliacao(
    payload: AvaliacaoCreateSchema,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    """
    Submete uma avaliação para uma estadia.
    Critérios de Aceite:
    - Reserva confirmada
    - Check-out no passado (viagem finalizada)
    - Reserva pertencente ao usuário logado
    - Máximo de 1 avaliação por reserva
    """

    service = AvaliacaoService(db, mongo_db)
    return await service.registrar_avaliacao(payload, usuario_atual)


@router.get(
    "/hotel/{hotel_id}",
    response_model=List[AvaliacaoResponseSchema],
    summary="Lista avaliações e comentários públicos de um hotel",
)
def listar_avaliacoes_hotel(
    hotel_id: uuid.UUID,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = AvaliacaoService(db, mongo_db)
    return service.listar_avaliacoes_hotel(hotel_id)


@router.get(
    "/hotel/{hotel_id}/resumo",
    response_model=HotelMediaAvaliacoesSchema,
    summary="Retorna média aritmética das avaliações e quantidade total",
)
def obter_resumo_hotel(
    hotel_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    repo = AvaliacaoRepository(db)
    media, total = repo.calcular_estatisticas_hotel(hotel_id)
    return HotelMediaAvaliacoesSchema(hotel_id=hotel_id, media=media, total_avaliacoes=total)


@router.get(
    "/reserva/{reserva_id}",
    response_model=AvaliacaoResponseSchema,
    summary="Consulta a avaliação realizada para uma reserva",
)
def obter_avaliacao_reserva(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    repo = AvaliacaoRepository(db)
    avaliacao = repo.get_by_reserva_id(reserva_id)
    if not avaliacao:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma avaliação encontrada para esta reserva.",
        )
    return avaliacao
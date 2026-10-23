import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rabbitmq import publish_event
from app.repositories.reserva_repository import ReservaRepository
from app.schemas.reserva import (
    ReservaAceitaSchema,
    ReservaCreateSchema,
    ReservaStatusSchema,
)

router = APIRouter(tags=["Reservas Assíncronas (Sprint 6)"])
FILA_SOLICITACOES = "solicitacoes-reserva"


@router.post(
    "/reservas",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReservaAceitaSchema,
    summary="Cria uma solicitação de reserva assíncrona (RFO06)",
)
async def criar_reserva(
    payload: ReservaCreateSchema,
    db: Session = Depends(get_db),
):
    """Persiste como Pendente, publica na fila e responde HTTP 202."""
    repo = ReservaRepository(db)
    reserva = repo.create(
        quarto_id=payload.quarto_id,
        checkin=payload.checkin,
        checkout=payload.checkout,
        adultos=payload.adultos,
        criancas=payload.criancas,
        bebes=payload.bebes,
        valor_total=payload.valor_total,
        cotacao_snapshot=payload.cotacao_snapshot,
    )

    await publish_event(
        FILA_SOLICITACOES,
        {
            "reserva_id": str(reserva.id),
            "quarto_id": str(reserva.quarto_id),
            "checkin": reserva.checkin.isoformat(),
            "checkout": reserva.checkout.isoformat(),
            "adultos": reserva.adultos,
            "criancas": reserva.criancas,
            "bebes": reserva.bebes,
            "valor_total": reserva.valor_total,
        },
    )

    return ReservaAceitaSchema(id=reserva.id, status=reserva.status)


@router.get(
    "/reservas/{reserva_id}",
    response_model=ReservaStatusSchema,
    summary="Consulta o status da reserva (short polling — RFO06)",
)
def obter_status_reserva(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retorna o estado atual da reserva para o polling do frontend."""
    reserva = ReservaRepository(db).get_by_id(reserva_id)
    if reserva is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva '{reserva_id}' não encontrada.",
        )
    return reserva
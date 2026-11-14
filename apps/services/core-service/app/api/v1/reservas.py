import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rabbitmq import publish_event
from app.models.hotel import Quarto
from app.models.usuario import Usuario
from app.repositories.reserva_repository import ReservaRepository
from app.schemas.reserva import (
    ReservaAceitaSchema,
    ReservaCreateSchema,
    ReservaDetalheSchema,
    ReservaListItemSchema,
)

router = APIRouter(tags=["Painel de Reservas & Hóspede (Sprint 7)"])

FILA_SOLICITACOES = "solicitacoes-reserva"


@router.get(
    "/reservas",
    response_model=List[ReservaListItemSchema],
    summary="Lista todas as reservas do hóspede logado",
)
def listar_minhas_reservas(
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    """
    Retorna o histórico completo de reservas do usuário logado,
    ordenado pela mais recente, com informações de hotel e quarto para exibição em cards.
    """
    repo = ReservaRepository(db)
    reservas = repo.list_by_usuario_id(usuario_atual.id)

    itens = []
    for r in reservas:
        hotel_nome = r.quarto.hotel.nome if r.quarto and r.quarto.hotel else "Hotel Não Identificado"
        cidade_nome = (
            r.quarto.hotel.cidade.nome
            if r.quarto and r.quarto.hotel and r.quarto.hotel.cidade
            else "Localização"
        )
        quarto_numero = r.quarto.numero if r.quarto else "-"
        quarto_tipo = r.quarto.tipo if r.quarto else "Standard"

        itens.append(
            ReservaListItemSchema(
                id=r.id,
                usuario_id=r.usuario_id,
                quarto_id=r.quarto_id,
                checkin=r.checkin,
                checkout=r.checkout,
                adultos=r.adultos,
                criancas=r.criancas,
                bebes=r.bebes,
                valor_total=r.valor_total,
                status=r.status,
                criado_em=r.criado_em,
                atualizado_em=r.atualizado_em,
                hotel_nome=hotel_nome,
                cidade_nome=cidade_nome,
                quarto_numero=quarto_numero,
                quarto_tipo=quarto_tipo,
            )
        )
    return itens


@router.post(
    "/reservas",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ReservaAceitaSchema,
    summary="Cria solicitação de reserva assíncrona com validação de capacidade",
)
async def criar_reserva(
    payload: ReservaCreateSchema,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    """
    Hardening aplicado:
    1. Validação de datas: checkin não pode ser no passado; checkout deve ser posterior ao checkin.
    2. Validação de capacidade: confere capacidade do quarto (adultos e crianças).
    3. Vincula obrigatoriamente a reserva ao ID do usuário autenticado.
    """
    hoje = date.today()
    if payload.checkin < hoje:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de check-in não pode ser anterior à data de hoje.",
        )

    if payload.checkout <= payload.checkin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data de check-out deve ser obrigatoriamente posterior à data de check-in.",
        )

    quarto = db.query(Quarto).filter(Quarto.id == payload.quarto_id).first()
    if not quarto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quarto com ID '{payload.quarto_id}' não foi encontrado.",
        )

    if not quarto.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O quarto selecionado está temporariamente desativado para reservas.",
        )

    if payload.adultos > quarto.max_adultos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Capacidade excedida: Este quarto acomoda no máximo {quarto.max_adultos} adulto(s). "
                f"Solicitado: {payload.adultos}."
            ),
        )

    if payload.criancas > quarto.max_criancas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Capacidade excedida: Este quarto acomoda no máximo {quarto.max_criancas} criança(s). "
                f"Solicitado: {payload.criancas}."
            ),
        )

    repo = ReservaRepository(db)

    reserva = repo.create(
        usuario_id=usuario_atual.id,
        quarto_id=payload.quarto_id,
        checkin=payload.checkin,
        checkout=payload.checkout,
        adultos=payload.adultos,
        criancas=payload.criancas,
        bebes=payload.bebes,
        valor_total=payload.valor_total,
        cotacao_snapshot=payload.cotacao_snapshot,
        status="Pendente",
    )

    evento = {
        "reserva_id": str(reserva.id),
        "usuario_id": str(reserva.usuario_id),
        "quarto_id": str(reserva.quarto_id),
        "checkin": reserva.checkin.isoformat(),
        "checkout": reserva.checkout.isoformat(),
        "adultos": reserva.adultos,
        "criancas": reserva.criancas,
        "bebes": reserva.bebes,
        "valor_total": reserva.valor_total,
    }
    await publish_event(FILA_SOLICITACOES, evento)

    return ReservaAceitaSchema(
        id=reserva.id,
        status=reserva.status,
        mensagem="Reserva recebida e em processamento. Acompanhe pelo Painel de Reservas.",
    )


@router.get(
    "/reservas/{reserva_id}",
    response_model=ReservaDetalheSchema,
    summary="Consulta detalhes de uma reserva específica (requer permissão)",
)
def obter_detalhes_reserva(
    reserva_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario_atual: Usuario = Depends(get_current_user),
):
    """
    Retorna os detalhes completos da reserva.
    Segurança: Hóspede só pode consultar reservas que pertencem a ele mesmo.
    Admins podem consultar qualquer reserva.
    """
    repo = ReservaRepository(db)
    reserva = repo.get_by_id_with_relations(reserva_id)

    if not reserva:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reserva com identificador '{reserva_id}' não encontrada.",
        )

    if reserva.usuario_id != usuario_atual.id and not usuario_atual.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: Você não possui autorização para visualizar os detalhes desta reserva.",
        )

    return reserva
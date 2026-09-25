import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.hotel import (
    HotelCreateSchema,
    HotelDetalhesResponseSchema,
    HotelResponseSchema,
)
from app.services.hotel_service import (
    CidadeNaoEncontradaError,
    HotelNaoEncontradoError,
    HotelService,
)

router = APIRouter(prefix="/hoteis", tags=["Hoteis"])


@router.post(
    "",
    response_model=HotelResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um hotel vinculado a uma cidade",
)
def criar_hotel(
    payload: HotelCreateSchema,
    db: Session = Depends(get_db),
):
    service = HotelService(db)
    try:
        return service.repository.create(
            nome=payload.nome,
            cidade_id=payload.cidade_id,
            categoria_estrelas=payload.categoria_estrelas,
        )
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "",
    response_model=List[HotelResponseSchema],
    summary="Lista os hotéis com cidade aninhada e comodidades",
)
def listar_hoteis(
    cidade_id: Optional[uuid.UUID] = Query(
        default=None, description="Filtra os hotéis por cidade"
    ),
    db: Session = Depends(get_db),
):
    try:
        return HotelService(db).listar(cidade_id=cidade_id)
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{hotel_id}",
    response_model=HotelDetalhesResponseSchema,
    summary="Retorna os detalhes do hotel com seus quartos e capacidades",
)
def obter_detalhes_hotel(
    hotel_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = HotelService(db)
    try:
        return service.buscar_por_id(hotel_id)
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
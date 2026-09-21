import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.hotel_service import (
    CidadeNaoEncontradaError,
    ComodidadeNaoEncontradaError,
    HotelNaoEncontradoError,
    HotelService,
)

router = APIRouter(prefix="/admin/hoteis", tags=["Admin - Hotéis"])




class HotelCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1, max_length=150)
    cidade_id: uuid.UUID
    categoria_estrelas: Optional[int] = Field(None, ge=1, le=5)


class HotelUpdateRequest(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=150)
    cidade_id: Optional[uuid.UUID] = None
    categoria_estrelas: Optional[int] = Field(None, ge=1, le=5)


class ComodidadeNestedResponse(BaseModel):
    id: uuid.UUID
    nome: str

    class Config:
        from_attributes = True


class HotelResponse(BaseModel):
    id: uuid.UUID
    nome: str
    cidade_id: uuid.UUID
    categoria_estrelas: Optional[int] = None
    comodidades: List[ComodidadeNestedResponse] = []

    class Config:
        from_attributes = True




@router.post("", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
def criar_hotel(payload: HotelCreateRequest, db: Session = Depends(get_db)):
    service = HotelService(db)
    try:
        return service.criar(
            nome=payload.nome,
            cidade_id=payload.cidade_id,
            categoria_estrelas=payload.categoria_estrelas,
        )
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[HotelResponse])
def listar_hoteis(
    cidade_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    service = HotelService(db)
    try:
        return service.listar(cidade_id=cidade_id)
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{hotel_id}", response_model=HotelResponse)
def buscar_hotel(hotel_id: uuid.UUID, db: Session = Depends(get_db)):
    service = HotelService(db)
    try:
        return service.buscar_por_id(hotel_id)
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{hotel_id}", response_model=HotelResponse)
def atualizar_hotel(
    hotel_id: uuid.UUID,
    payload: HotelUpdateRequest,
    db: Session = Depends(get_db),
):
    service = HotelService(db)
    try:
        dados = payload.model_dump(exclude_unset=True)
        return service.atualizar(hotel_id, dados)
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_hotel(hotel_id: uuid.UUID, db: Session = Depends(get_db)):
    service = HotelService(db)
    try:
        service.remover(hotel_id)
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{hotel_id}/comodidades/{comodidade_id}", response_model=HotelResponse)
def adicionar_comodidade(
    hotel_id: uuid.UUID,
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = HotelService(db)
    try:
        return service.adicionar_comodidade(hotel_id, comodidade_id)
    except (HotelNaoEncontradoError, ComodidadeNaoEncontradaError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{hotel_id}/comodidades/{comodidade_id}", response_model=HotelResponse)
def remover_comodidade(
    hotel_id: uuid.UUID,
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    service = HotelService(db)
    try:
        return service.remover_comodidade(hotel_id, comodidade_id)
    except (HotelNaoEncontradoError, ComodidadeNaoEncontradaError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
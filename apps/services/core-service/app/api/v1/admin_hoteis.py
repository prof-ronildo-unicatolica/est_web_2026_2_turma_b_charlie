import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db, get_mongo_db
from app.models.usuario import Usuario
from app.schemas.hotel import HotelCreateSchema, HotelResponseSchema, HotelUpdateSchema
from app.services.hotel_service import (
    CidadeNaoEncontradaError,
    ComodidadeNaoEncontradaError,
    HotelNaoEncontradoError,
    HotelService,
)

router = APIRouter(prefix="/admin/hoteis", tags=["Admin — Hoteis"])


@router.post(
    "",
    response_model=HotelResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Cria um hotel vinculado a uma cidade",
)
async def criar_hotel(
    payload: HotelCreateSchema,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = HotelService(db, mongo_db)
    try:
        return await service.criar(
            nome=payload.nome,
            cidade_id=payload.cidade_id,
            categoria_estrelas=payload.categoria_estrelas,
        )
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{hotel_id}",
    response_model=HotelResponseSchema,
    summary="[ADMIN] Atualiza um hotel existente",
)
async def atualizar_hotel(
    hotel_id: uuid.UUID,
    payload: HotelUpdateSchema,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = HotelService(db, mongo_db)
    try:
        return await service.atualizar(hotel_id, payload.model_dump(exclude_none=True))
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{hotel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove um hotel",
)
async def remover_hotel(
    hotel_id: uuid.UUID,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = HotelService(db, mongo_db)
    try:
        await service.remover(hotel_id)
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{hotel_id}/comodidades/{comodidade_id}",
    response_model=HotelResponseSchema,
    summary="[ADMIN] Associa uma comodidade a um hotel",
)
async def adicionar_comodidade(
    hotel_id: uuid.UUID,
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = HotelService(db, mongo_db)
    try:
        return await service.adicionar_comodidade(hotel_id, comodidade_id)
    except (HotelNaoEncontradoError, ComodidadeNaoEncontradaError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/{hotel_id}/comodidades/{comodidade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove a associacao de uma comodidade ao hotel",
)
async def remover_comodidade_do_hotel(
    hotel_id: uuid.UUID,
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = HotelService(db, mongo_db)
    try:
        await service.remover_comodidade(hotel_id, comodidade_id)
    except (HotelNaoEncontradoError, ComodidadeNaoEncontradaError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
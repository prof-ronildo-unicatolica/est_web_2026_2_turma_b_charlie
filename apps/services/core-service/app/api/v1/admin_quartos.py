import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db, get_mongo_db
from app.models.usuario import Usuario
from app.schemas.hotel import QuartoCreateSchema, QuartoResponseSchema, QuartoUpdateSchema
from app.services.catalogo_mongo_service import CatalogoMongoService
from app.services.hotel_service import (
    CapacidadeInvalidaError,
    HotelNaoEncontradoError,
    QuartoNaoEncontradoError,
    QuartoNumeroDuplicadoError,
    QuartoService,
)

router = APIRouter(prefix="/admin", tags=["Admin — Quartos & Catálogo"])


@router.post(
    "/quartos",
    response_model=QuartoResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Cria um quarto e sincroniza o MongoDB",
)
async def criar_quarto(
    payload: QuartoCreateSchema,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = QuartoService(db, mongo_db)
    try:
        return await service.criar(
            hotel_id=payload.hotel_id,
            numero=payload.numero,
            tipo=payload.tipo,
            preco_diaria=payload.preco_diaria,
            max_adultos=payload.max_adultos,
            max_criancas=payload.max_criancas,
            descricao=payload.descricao,
            ativo=payload.ativo,
        )
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuartoNumeroDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CapacidadeInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/quartos",
    response_model=List[QuartoResponseSchema],
    summary="[ADMIN] Lista quartos (com filtro opcional por hotel)",
)
def listar_quartos(
    hotel_id: Optional[uuid.UUID] = Query(default=None, description="Filtrar por hotel"),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = QuartoService(db)
    try:
        if hotel_id:
            return service.listar_por_hotel(hotel_id)
        return service.listar_todos()
    except HotelNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/quartos/{quarto_id}",
    response_model=QuartoResponseSchema,
    summary="[ADMIN] Busca um quarto pelo ID",
)
def buscar_quarto(
    quarto_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = QuartoService(db)
    try:
        return service.buscar_por_id(quarto_id)
    except QuartoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/quartos/{quarto_id}",
    response_model=QuartoResponseSchema,
    summary="[ADMIN] Atualiza dados do quarto e sincroniza MongoDB",
)
async def atualizar_quarto(
    quarto_id: uuid.UUID,
    payload: QuartoUpdateSchema,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = QuartoService(db, mongo_db)
    try:
        return await service.atualizar(quarto_id, payload.model_dump(exclude_none=True))
    except QuartoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except QuartoNumeroDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except CapacidadeInvalidaError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/quartos/{quarto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove um quarto e atualiza o MongoDB",
)
async def remover_quarto(
    quarto_id: uuid.UUID,
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = QuartoService(db, mongo_db)
    try:
        await service.remover(quarto_id)
    except QuartoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/catalogo/rebuild",
    summary="[ADMIN] Força a reconstrução de toda a projeção no MongoDB",
)
async def rebuild_catalogo_mongo(
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = CatalogoMongoService(mongo_db, db)
    total = await service.reconstruir_todo_catalogo()
    return {"message": "Catálogo do MongoDB reconstruído com sucesso.", "total_hoteis_sincronizados": total}
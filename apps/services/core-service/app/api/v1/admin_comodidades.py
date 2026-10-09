import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.hotel import (
    ComodidadeCreateSchema,
    ComodidadeResponseSchema,
    ComodidadeUpdateSchema,
)
from app.services.hotel_service import (
    ComodidadeJaExisteError,
    ComodidadeNaoEncontradaError,
    ComodidadeService,
)

router = APIRouter(prefix="/admin/comodidades", tags=["Admin — Comodidades"])


@router.get(
    "",
    response_model=List[ComodidadeResponseSchema],
    summary="[ADMIN] Lista todas as comodidades",
)
def listar_comodidades(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    return ComodidadeService(db).listar()


@router.post(
    "",
    response_model=ComodidadeResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Cria uma nova comodidade",
)
def criar_comodidade(
    payload: ComodidadeCreateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ComodidadeService(db)
    try:
        return service.criar(nome=payload.nome)
    except ComodidadeJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put(
    "/{comodidade_id}",
    response_model=ComodidadeResponseSchema,
    summary="[ADMIN] Atualiza uma comodidade existente",
)
def atualizar_comodidade(
    comodidade_id: uuid.UUID,
    payload: ComodidadeUpdateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ComodidadeService(db)
    try:
        return service.atualizar(comodidade_id, nome=payload.nome)
    except ComodidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ComodidadeJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{comodidade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove uma comodidade",
)
def remover_comodidade(
    comodidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = ComodidadeService(db)
    try:
        service.remover(comodidade_id)
    except ComodidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
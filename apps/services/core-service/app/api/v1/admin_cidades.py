import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.hotel import CidadeCreateSchema, CidadeResponseSchema, CidadeUpdateSchema
from app.services.hotel_service import (
    CidadeJaExisteError,
    CidadeNaoEncontradaError,
    CidadeService,
)

router = APIRouter(prefix="/admin/cidades", tags=["Admin — Cidades"])


@router.post(
    "",
    response_model=CidadeResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Cria uma nova cidade",
)
def criar_cidade(
    payload: CidadeCreateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = CidadeService(db)
    try:
        return service.criar(
            nome=payload.nome,
            limite_territorial=payload.limite_territorial,
        )
    except CidadeJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put(
    "/{cidade_id}",
    response_model=CidadeResponseSchema,
    summary="[ADMIN] Atualiza uma cidade existente",
)
def atualizar_cidade(
    cidade_id: uuid.UUID,
    payload: CidadeUpdateSchema,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = CidadeService(db)
    try:
        return service.atualizar(cidade_id, payload.model_dump(exclude_none=True))
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CidadeJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{cidade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[ADMIN] Remove uma cidade (cascade nos hoteis vinculados)",
)
def remover_cidade(
    cidade_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(get_current_admin),
):
    service = CidadeService(db)
    try:
        service.remover(cidade_id)
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.hotel_service import (
    CidadeJaExisteError,
    CidadeNaoEncontradaError,
    CidadeService,
)

router = APIRouter(prefix="/admin/cidades", tags=["Admin - Cidades"])




class CidadeCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    limite_territorial: Optional[dict] = None


class CidadeUpdateRequest(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    limite_territorial: Optional[dict] = None


class CidadeResponse(BaseModel):
    id: uuid.UUID
    nome: str
    limite_territorial: Optional[dict] = None

    class Config:
        from_attributes = True




@router.post("", response_model=CidadeResponse, status_code=status.HTTP_201_CREATED)
def criar_cidade(payload: CidadeCreateRequest, db: Session = Depends(get_db)):
    service = CidadeService(db)
    try:
        return service.criar(
            nome=payload.nome,
            limite_territorial=payload.limite_territorial,
        )
    except CidadeJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[CidadeResponse])
def listar_cidades(db: Session = Depends(get_db)):
    service = CidadeService(db)
    return service.listar()


@router.get("/{cidade_id}", response_model=CidadeResponse)
def buscar_cidade(cidade_id: uuid.UUID, db: Session = Depends(get_db)):
    service = CidadeService(db)
    try:
        return service.buscar_por_id(cidade_id)
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{cidade_id}", response_model=CidadeResponse)
def atualizar_cidade(
    cidade_id: uuid.UUID,
    payload: CidadeUpdateRequest,
    db: Session = Depends(get_db),
):
    service = CidadeService(db)
    try:
        dados = payload.model_dump(exclude_unset=True)
        return service.atualizar(cidade_id, dados)
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CidadeJaExisteError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{cidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_cidade(cidade_id: uuid.UUID, db: Session = Depends(get_db)):
    service = CidadeService(db)
    try:
        service.remover(cidade_id)
    except CidadeNaoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
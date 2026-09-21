import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# comodidade 

class ComodidadeCreateSchema(BaseModel):
    """ Payload de criação de comodidade """
    nome: str = Field(min_length=1, max_length=100)


class ComodidadeUpdateSchema(BaseModel):
    """ Payload de atualização de comodidade"""
    nome: str = Field(min_length=1, max_length=100)


class ComodidadeResponseSchema(BaseModel):
    """Contrato de resposta da API para Comodidade """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str


# cidade

class CidadeCreateSchema(BaseModel):
    """Payload de criação de cidade """

    nome: str = Field(min_length=1, max_length=100)
    limite_territorial: Optional[Dict[str, Any]] = None


class CidadeUpdateSchema(BaseModel):
    """ Payload de atualização parcial de cidade """

    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    limite_territorial: Optional[Dict[str, Any]] = None


class CidadeResponseSchema(BaseModel):
    """ Contrato de resposta da API para Cidade """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    limite_territorial: Optional[Dict[str, Any]] = None


# hotel

class HotelCreateSchema(BaseModel):
    """ Payload de criação de hotel """

    nome: str = Field(min_length=1, max_length=100)
    cidade_id: uuid.UUID
    categoria_estrelas: Optional[int] = Field(default=None, ge=1, le=5)


class HotelUpdateSchema(BaseModel):
    """ Payload de atualização parcial de hotel  """

    nome: Optional[str] = Field(default=None, min_length=1, max_length=100)
    cidade_id: Optional[uuid.UUID] = None
    categoria_estrelas: Optional[int] = Field(default=None, ge=1, le=5)


class HotelResponseSchema(BaseModel):
    """  Resposta com Cidade aninhada e lista de Comodidades """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    categoria_estrelas: Optional[int] = None
    cidade: CidadeResponseSchema
    comodidades: List[ComodidadeResponseSchema] = []



class CidadeComHoteisSchema(CidadeResponseSchema):
    """ Schema opcional para listagem de cidade com seus hotéis """
    hoteis: List[HotelResponseSchema] = []
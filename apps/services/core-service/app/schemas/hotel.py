import uuid
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class CidadeCreateSchema(BaseModel):
    """Payload de entrada para criação de cidade (não aceita id)."""

    nome: str = Field(min_length=1, max_length=100)


class CidadeResponseSchema(BaseModel):
    """Contrato de resposta da API com id gerado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str


class HotelCreateSchema(BaseModel):
    """Payload de entrada: recebe cidade_id como UUID."""

    nome: str = Field(min_length=1, max_length=100)
    cidade_id: uuid.UUID


class HotelResponseSchema(BaseModel):
    """Resposta com o objeto Cidade aninhado."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    cidade: CidadeResponseSchema


class CidadeComHoteisSchema(CidadeResponseSchema):
    """Schema opcional para listagem de cidade com seus hotéis."""

    hoteis: List[HotelResponseSchema] = []

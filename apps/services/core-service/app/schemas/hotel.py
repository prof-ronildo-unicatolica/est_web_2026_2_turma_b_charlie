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



# quarto

class QuartoCreateSchema(BaseModel):
    numero: str = Field(min_length=1, max_length=20, examples=["101"])
    tipo: str = Field(min_length=2, max_length=50, examples=["Casal Luxo", "Standard", "Família"])
    preco_diaria: float = Field(gt=0, examples=[250.0])
    max_adultos: int = Field(ge=1, le=10, default=2, examples=[2])
    max_criancas: int = Field(ge=0, le=10, default=0, examples=[1])
    descricao: Optional[str] = Field(default=None, max_length=500)
    hotel_id: uuid.UUID
    ativo: bool = True


class QuartoUpdateSchema(BaseModel):
    numero: Optional[str] = Field(default=None, min_length=1, max_length=20)
    tipo: Optional[str] = Field(default=None, min_length=2, max_length=50)
    preco_diaria: Optional[float] = Field(default=None, gt=0)
    max_adultos: Optional[int] = Field(default=None, ge=1, le=10)
    max_criancas: Optional[int] = Field(default=None, ge=0, le=10)
    descricao: Optional[str] = Field(default=None, max_length=500)
    ativo: Optional[bool] = None


class QuartoResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero: str
    tipo: str
    preco_diaria: float
    max_adultos: int
    max_criancas: int
    descricao: Optional[str] = None
    ativo: bool
    hotel_id: uuid.UUID



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


class HotelDetalhesResponseSchema(HotelResponseSchema):
    quartos: List[QuartoResponseSchema] = []



class CatalogoHotelItemSchema(BaseModel):
    hotel_id: str
    nome: str
    categoria_estrelas: Optional[int] = None
    cidade_nome: str
    cidade_id: str
    comodidades: List[str] = []
    preco_minimo: float
    capacidade_maxima_adultos: int
    capacidade_maxima_criancas: int
    total_quartos_ativos: int
    quartos_disponiveis: List[Dict[str, Any]] = []


class BuscaCatalogoResponseSchema(BaseModel):
    total: int
    filtros_aplicados: Dict[str, Any]
    hoteis: List[CatalogoHotelItemSchema]
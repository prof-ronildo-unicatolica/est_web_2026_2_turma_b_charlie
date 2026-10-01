import uuid
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TarifaTemporadaBaseSchema(BaseModel):
    nome: str = Field(..., max_length=100, examples=["Alta Estação Verão"])
    data_inicio: date
    data_fim: date
    multiplicador: float = Field(..., gt=0, examples=[1.5])
    ativo: bool = True


class TarifaTemporadaCreateSchema(TarifaTemporadaBaseSchema):
    hotel_id: uuid.UUID


class TarifaTemporadaUpdateSchema(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    multiplicador: Optional[float] = Field(None, gt=0)
    ativo: Optional[bool] = None


class TarifaTemporadaResponseSchema(TarifaTemporadaBaseSchema):
    id: uuid.UUID
    hotel_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ServicoAdicionalBaseSchema(BaseModel):
    nome: str = Field(..., max_length=100, examples=["Café da Manhã Buffet"])
    descricao: Optional[str] = None
    preco: float = Field(..., ge=0, examples=[35.0])
    por_diaria: bool = Field(True, description="True se o valor é por diária, False se taxa fixa por estadia")
    ativo: bool = True


class ServicoAdicionalCreateSchema(ServicoAdicionalBaseSchema):
    hotel_id: uuid.UUID


class ServicoAdicionalUpdateSchema(BaseModel):
    nome: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = None
    preco: Optional[float] = Field(None, ge=0)
    por_diaria: Optional[bool] = None
    ativo: Optional[bool] = None


class ServicoAdicionalResponseSchema(ServicoAdicionalBaseSchema):
    id: uuid.UUID
    hotel_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class CotacaoRequestSchema(BaseModel):
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int = Field(default=1, ge=1, description="Mínimo 1 adulto")
    criancas: int = Field(default=0, ge=0, description="Idade 6 a 12 anos (50% diária base)")
    bebes: int = Field(default=0, ge=0, description="Idade 0 a 5 anos (Grátis)")
    early_checkin: bool = Field(default=False, description="+30% de 1 diária base")
    late_checkout: bool = Field(default=False, description="+30% de 1 diária base")
    tipo_tarifa: str = Field(default="reembolsavel", description="'reembolsavel' ou 'nao_reembolsavel' (-10% desconto)")
    servicos_adicionais_ids: List[uuid.UUID] = Field(default_factory=list)


class DetalheDiariaSchema(BaseModel):
    data: date
    preco_base: float
    multiplicador_temporada: float
    valor_final: float
    tarifa_aplicada: Optional[str] = None


class ItemServicoCalculadoSchema(BaseModel):
    id: uuid.UUID
    nome: str
    preco_unitario: float
    por_diaria: bool
    quantidade_dias: int
    valor_total: float


class CotacaoResponseSchema(BaseModel):
    quarto_id: uuid.UUID
    quarto_tipo: str
    quarto_numero: str
    preco_base_diaria: float
    checkin: date
    checkout: date
    num_diarias: int
    adultos: int
    criancas: int
    bebes: int
    diarias: List[DetalheDiariaSchema]
    subtotal_diarias: float
    adicional_criancas: float
    valor_bebes: float = 0.0
    taxa_early_checkin: float
    taxa_late_checkout: float
    subtotal_estadia: float
    desconto_nao_reembolsavel: float
    servicos_selecionados: List[ItemServicoCalculadoSchema]
    total_servicos_adicionais: float
    valor_total: float
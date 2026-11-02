import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
)


class ReservaHotelResumo(BaseModel):
    id: uuid.UUID
    nome: str
    categoria_estrelas: Optional[int] = None
    # No ORM, a cidade é um relacionamento Hotel.cidade, não cidade_nome.
    cidade_nome: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "cidade_nome",
            AliasPath("cidade", "nome"),
        ),
    )

    model_config = ConfigDict(from_attributes=True)


class ReservaQuartoResumo(BaseModel):
    id: uuid.UUID
    numero: str
    tipo: str
    preco_diaria: float
    max_adultos: int
    max_criancas: int
    hotel: Optional[ReservaHotelResumo] = None

    model_config = ConfigDict(from_attributes=True)


class ReservaCreateSchema(BaseModel):
    """Payload do frontend ao confirmar reserva."""
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int = Field(default=1, ge=1, description="Mínimo 1 adulto")
    criancas: int = Field(default=0, ge=0)
    bebes: int = Field(default=0, ge=0)
    valor_total: float = Field(..., gt=0)
    cotacao_snapshot: Optional[Dict[str, Any]] = None


class ReservaAceitaSchema(BaseModel):
    """Resposta do POST /reservas (HTTP 202)."""
    id: uuid.UUID
    status: str = "Pendente"
    mensagem: str = "Reserva recebida e em processamento. Acompanhe pelo Painel de Reservas."


class ReservaListItemSchema(BaseModel):
    """Item compacto da lista de reservas do hóspede."""
    id: uuid.UUID
    usuario_id: uuid.UUID
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int
    criancas: int
    bebes: int
    valor_total: float
    status: str
    criado_em: datetime
    atualizado_em: datetime
    hotel_nome: str
    cidade_nome: str
    quarto_numero: str
    quarto_tipo: str

    model_config = ConfigDict(from_attributes=True)


class ReservaDetalheSchema(BaseModel):
    """Detalhes da reserva usados pelo voucher e short polling."""
    id: uuid.UUID
    usuario_id: uuid.UUID
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int
    criancas: int
    bebes: int
    valor_total: float
    status: str
    cotacao_snapshot: Optional[Dict[str, Any]] = None
    criado_em: datetime
    atualizado_em: datetime
    quarto: Optional[ReservaQuartoResumo] = None

    model_config = ConfigDict(from_attributes=True)


# Mantém compatibilidade com o endpoint de short polling da Sprint 6.
ReservaStatusSchema = ReservaDetalheSchema

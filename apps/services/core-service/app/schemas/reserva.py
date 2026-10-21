import uuid
from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReservaCreateSchema(BaseModel):
    """Payload do frontend ao confirmar reserva."""
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int = Field(default=1, ge=1)
    criancas: int = Field(default=0, ge=0)
    bebes: int = Field(default=0, ge=0)
    valor_total: float = Field(..., gt=0)
    cotacao_snapshot: Optional[Dict[str, Any]] = None 


class ReservaAceitaSchema(BaseModel):
    """Resposta do POST /reservas (HTTP 202)."""
    id: uuid.UUID
    status: str
    mensagem: str = "Reserva recebida e em processamento. Acompanhe pelo ID."


class ReservaStatusSchema(BaseModel):
    """Resposta do GET /reservas/{id} — usado pelo short polling."""
    id: uuid.UUID
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

    model_config = ConfigDict(from_attributes=True)
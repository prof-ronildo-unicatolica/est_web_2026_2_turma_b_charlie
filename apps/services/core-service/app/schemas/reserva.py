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
    # Preserva a leitura da cidade pelo relacionamento Hotel.cidade.nome.
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
    tipo_tarifa: str = Field(
        default="reembolsavel",
        description="'reembolsavel' ou 'nao_reembolsavel'",
    )
    cotacao_snapshot: Optional[Dict[str, Any]] = None


class ReservaAceitaSchema(BaseModel):
    """Resposta do POST /reservas (HTTP 202)."""
    id: uuid.UUID
    status: str = "Pendente"
    mensagem: str = "Reserva recebida e em processamento. Acompanhe pelo Painel de Reservas."


class CancelamentoRequestSchema(BaseModel):
    """Corpo da solicitação de cancelamento."""
    motivo: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Motivo opcional do cancelamento fornecido pelo hóspede",
    )


class CancelamentoPreviewResponseSchema(BaseModel):
    """Simulação das multas antes da confirmação do cancelamento."""
    reserva_id: uuid.UUID
    tipo_tarifa: str
    checkin: date
    data_limite_cancelamento: datetime
    dentro_do_prazo: bool
    horas_ate_checkin: float
    valor_total: float
    valor_multa: float
    valor_reembolso: float
    cenario_identificado: str
    mensagem_politica: str


class CancelamentoResponseSchema(BaseModel):
    """Resultado da efetivação do cancelamento."""
    id: uuid.UUID
    status: str = "Cancelada"
    tipo_tarifa: str
    valor_total: float
    valor_multa: float
    valor_reembolso: float
    cancelado_em: datetime
    motivo: Optional[str] = None
    mensagem: str


class ReservaListItemSchema(BaseModel):
    """Item da lista Minhas Reservas com valores e política de cancelamento."""
    id: uuid.UUID
    usuario_id: uuid.UUID
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int
    criancas: int
    bebes: int
    valor_total: float
    tipo_tarifa: str
    status: str
    criado_em: datetime
    atualizado_em: datetime
    data_limite_cancelamento: datetime
    pode_cancelar: bool
    valor_multa: Optional[float] = 0.0
    valor_reembolso: Optional[float] = 0.0
    cancelado_em: Optional[datetime] = None
    hotel_nome: str
    cidade_nome: str
    quarto_numero: str
    quarto_tipo: str

    model_config = ConfigDict(from_attributes=True)


class ReservaDetalheSchema(BaseModel):
    """Detalhes completos da reserva e da política de cancelamento."""
    id: uuid.UUID
    usuario_id: uuid.UUID
    quarto_id: uuid.UUID
    checkin: date
    checkout: date
    adultos: int
    criancas: int
    bebes: int
    valor_total: float
    tipo_tarifa: str
    status: str
    valor_multa: Optional[float] = 0.0
    valor_reembolso: Optional[float] = 0.0
    cancelado_em: Optional[datetime] = None
    motivo_cancelamento: Optional[str] = None
    data_limite_cancelamento: datetime
    cotacao_snapshot: Optional[Dict[str, Any]] = None
    criado_em: datetime
    atualizado_em: datetime
    quarto: Optional[ReservaQuartoResumo] = None

    model_config = ConfigDict(from_attributes=True)


# Mantém compatibilidade com o endpoint de short polling da Sprint 6.
ReservaStatusSchema = ReservaDetalheSchema

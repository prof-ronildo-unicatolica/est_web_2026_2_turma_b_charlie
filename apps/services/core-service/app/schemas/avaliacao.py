import uuid
from datetime import datetime
from typing import Dict, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AvaliacaoCreateSchema(BaseModel):
    """Payload para registro de avaliação de uma reserva concluída."""

    reserva_id: uuid.UUID = Field(
        ...,
        description="ID da reserva concluída que será avaliada",
    )
    nota: int = Field(
        ...,
        ge=1,
        le=5,
        description="Nota de 1 a 5 estrelas",
    )
    comentario: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Comentário opcional do hóspede",
    )


class AutorResumoSchema(BaseModel):
    """Dados públicos mínimos do autor da avaliação."""

    id: uuid.UUID
    nome: str

    model_config = ConfigDict(from_attributes=True)


class AvaliacaoResponseSchema(BaseModel):
    """Resposta com os dados persistidos de uma avaliação."""

    id: uuid.UUID
    reserva_id: uuid.UUID
    hotel_id: uuid.UUID
    usuario_id: uuid.UUID
    nota: int
    comentario: Optional[str] = None
    criado_em: datetime
    autor: Optional[AutorResumoSchema] = Field(
        default=None,
        validation_alias=AliasChoices("autor", "usuario"),
    )

    model_config = ConfigDict(from_attributes=True)


class HotelMediaAvaliacoesSchema(BaseModel):
    """Resumo estatístico das avaliações de um hotel."""

    hotel_id: uuid.UUID
    media: float = Field(
        default=0.0,
        ge=0,
        le=5,
        description="Média aritmética das notas",
    )
    total_avaliacoes: int = Field(
        default=0,
        ge=0,
        description="Quantidade de avaliações recebidas",
    )
    distribuicao_notas: Optional[Dict[str, int]] = None

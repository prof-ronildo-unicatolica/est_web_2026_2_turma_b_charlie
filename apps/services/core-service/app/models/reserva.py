import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Boolean, Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base


class Reserva(Base):
    __tablename__ = "reservas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    quarto_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quartos.id", ondelete="CASCADE"), nullable=False
    )
    quarto: Mapped["Quarto"] = relationship("Quarto")  

    checkin: Mapped[date] = mapped_column(nullable=False)
    checkout: Mapped[date] = mapped_column(nullable=False)

    adultos: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    criancas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bebes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pendente")

    cotacao_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), nullable=True
    )

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
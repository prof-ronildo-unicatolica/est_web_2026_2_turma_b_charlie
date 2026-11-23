import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base


class Avaliacao(Base):
    """Avaliação de uma estadia concluída por um hóspede."""

    __tablename__ = "avaliacoes"
    __table_args__ = (
        CheckConstraint(
            "nota >= 1 AND nota <= 5",
            name="chk_avaliacao_nota_1_a_5",
        ),
        UniqueConstraint(
            "reserva_id",
            name="uq_avaliacoes_reserva_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    reserva_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reservas.id", ondelete="CASCADE"),
        nullable=False,
    )
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hoteis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nota: Mapped[int] = mapped_column(Integer, nullable=False)
    comentario: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    reserva: Mapped["Reserva"] = relationship("Reserva")
    hotel: Mapped["Hotel"] = relationship(
        "Hotel",
        back_populates="avaliacoes",
    )
    usuario: Mapped["Usuario"] = relationship("Usuario")

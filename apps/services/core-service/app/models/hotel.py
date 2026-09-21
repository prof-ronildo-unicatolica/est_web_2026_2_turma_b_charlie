import uuid
from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base


hotel_comodidade = Table(
    "hotel_comodidade",
    Base.metadata,
    Column(
        "hotel_id",
        ForeignKey("hoteis.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "comodidade_id",
        ForeignKey("comodidades.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)



class Comodidade(Base):
    __tablename__ = "comodidades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    hoteis: Mapped[List["Hotel"]] = relationship(
        secondary=hotel_comodidade, back_populates="comodidades"
    )



class Cidade(Base):
    __tablename__ = "cidades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    limite_territorial: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    hoteis: Mapped[List["Hotel"]] = relationship(
        back_populates="cidade", cascade="all, delete-orphan"
    )



class Hotel(Base):
    __tablename__ = "hoteis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)

    categoria_estrelas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    cidade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cidades.id", ondelete="CASCADE"), nullable=False
    )
    cidade: Mapped["Cidade"] = relationship(back_populates="hoteis")

    # NOVO: Relação M:N com Comodidade via tabela associativa
    comodidades: Mapped[List["Comodidade"]] = relationship(
        secondary=hotel_comodidade, back_populates="hoteis"
    )
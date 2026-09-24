import uuid
from typing import List, Optional

from sqlalchemy import Boolean, JSON, Column, ForeignKey, Integer, String, Table, Float, Text
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

    limite_territorial: Mapped[Optional[dict]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )

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

    
    comodidades: Mapped[List["Comodidade"]] = relationship(
        secondary=hotel_comodidade, back_populates="hoteis"
    )

    quartos: Mapped[List["Quarto"]] = relationship(
        back_populates="hotel", cascade="all, delete-orphan"
    )



class Quarto(Base):
    __tablename__ = "quartos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)  
    preco_diaria: Mapped[float] = mapped_column(Float, nullable=False)
    max_adultos: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    max_criancas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    
    hotel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hoteis.id", ondelete="CASCADE"), nullable=False
    )
    hotel: Mapped["Hotel"] = relationship(back_populates="quartos")
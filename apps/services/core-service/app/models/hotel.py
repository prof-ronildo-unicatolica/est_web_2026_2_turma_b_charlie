import uuid
from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.tutorial import Base


class Cidade(Base):
    __tablename__ = "cidades"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Lado 1 da relação (Navegação ORM em memória)
    hoteis: Mapped[List["Hotel"]] = relationship(
        back_populates="cidade", cascade="all, delete-orphan"
    )


class Hotel(Base):
    __tablename__ = "hoteis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)

    # Lado N da relação: FK real no banco de dados
    cidade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cidades.id", ondelete="CASCADE"), nullable=False
    )

    # Navegação reversa para o objeto Cidade
    cidade: Mapped["Cidade"] = relationship(back_populates="hoteis")
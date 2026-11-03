import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.hotel import Hotel, Quarto
from app.models.reserva import Reserva


class ReservaRepository:
    """Operações de persistência da entidade Reserva no PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        usuario_id: uuid.UUID,
        quarto_id: uuid.UUID,
        checkin: date,
        checkout: date,
        adultos: int,
        criancas: int,
        bebes: int,
        valor_total: float,
        cotacao_snapshot: Optional[dict] = None,
        status: str = "Pendente",
    ) -> Reserva:
        reserva = Reserva(
            usuario_id=usuario_id,
            quarto_id=quarto_id,
            checkin=checkin,
            checkout=checkout,
            adultos=adultos,
            criancas=criancas,
            bebes=bebes,
            valor_total=valor_total,
            cotacao_snapshot=cotacao_snapshot,
            status=status,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
        )
        self.db.add(reserva)
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def get_by_id(self, reserva_id: uuid.UUID) -> Optional[Reserva]:
        return self.db.query(Reserva).filter(Reserva.id == reserva_id).first()

    def get_by_id_with_relations(self, reserva_id: uuid.UUID) -> Optional[Reserva]:
        """Carrega Reserva -> Quarto -> Hotel -> Cidade em uma consulta."""
        return (
            self.db.query(Reserva)
            .options(
                joinedload(Reserva.quarto)
                .joinedload(Quarto.hotel)
                .joinedload(Hotel.cidade)
            )
            .filter(Reserva.id == reserva_id)
            .first()
        )

    def list_by_usuario_id(self, usuario_id: uuid.UUID) -> List[Reserva]:
        """Lista as reservas do usuário, da mais recente para a mais antiga."""
        return (
            self.db.query(Reserva)
            .options(
                joinedload(Reserva.quarto)
                .joinedload(Quarto.hotel)
                .joinedload(Hotel.cidade)
            )
            .filter(Reserva.usuario_id == usuario_id)
            .order_by(Reserva.criado_em.desc())
            .all()
        )

    def update_status(self, reserva: Reserva, novo_status: str) -> Reserva:
        reserva.status = novo_status
        reserva.atualizado_em = datetime.utcnow()
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def list_conflitos(
        self,
        quarto_id: uuid.UUID,
        checkin: date,
        checkout: date,
    ) -> List[Reserva]:
        """Busca reservas Confirmadas que se sobrepõem ao período — RNFO03."""
        return (
            self.db.query(Reserva)
            .filter(
                Reserva.quarto_id == quarto_id,
                Reserva.status == "Confirmada",
                Reserva.checkin < checkout,
                Reserva.checkout > checkin,
            )
            .all()
        )

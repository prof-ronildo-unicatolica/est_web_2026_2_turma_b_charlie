import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.reserva import Reserva


class ReservaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, quarto_id, checkin, checkout, adultos, criancas,
               bebes, valor_total, cotacao_snapshot=None, status="Pendente") -> Reserva:
        reserva = Reserva(
            quarto_id=quarto_id, checkin=checkin, checkout=checkout,
            adultos=adultos, criancas=criancas, bebes=bebes,
            valor_total=valor_total, cotacao_snapshot=cotacao_snapshot,
            status=status, criado_em=datetime.utcnow(), atualizado_em=datetime.utcnow(),
        )
        self.db.add(reserva)
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def get_by_id(self, reserva_id: uuid.UUID) -> Optional[Reserva]:
        return self.db.query(Reserva).filter(Reserva.id == reserva_id).first()

    def update_status(self, reserva: Reserva, novo_status: str) -> Reserva:
        reserva.status = novo_status
        reserva.atualizado_em = datetime.utcnow()
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def list_conflitos(self, quarto_id: uuid.UUID, checkin: date, checkout: date) -> List[Reserva]:
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
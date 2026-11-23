import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.avaliacao import Avaliacao


class AvaliacaoRepository:
    """Operações de persistência de avaliações no PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        reserva_id: uuid.UUID,
        hotel_id: uuid.UUID,
        usuario_id: uuid.UUID,
        nota: int,
        comentario: Optional[str] = None,
    ) -> Avaliacao:
        avaliacao = Avaliacao(
            reserva_id=reserva_id,
            hotel_id=hotel_id,
            usuario_id=usuario_id,
            nota=nota,
            comentario=comentario,
            criado_em=datetime.utcnow(),
        )
        self.db.add(avaliacao)
        try:
            self.db.commit()
        except SQLAlchemyError:
            # Libera a sessão para o serviço tratar, por exemplo, uma
            # violação de unicidade da reserva e responder com HTTP 409.
            self.db.rollback()
            raise
        self.db.refresh(avaliacao)
        return avaliacao

    def get_by_reserva_id(self, reserva_id: uuid.UUID) -> Optional[Avaliacao]:
        """Retorna a avaliação vinculada à reserva, se existir."""
        return (
            self.db.query(Avaliacao)
            .filter(Avaliacao.reserva_id == reserva_id)
            .first()
        )

    def list_by_hotel_id(
        self,
        hotel_id: uuid.UUID,
        limit: int = 50,
    ) -> List[Avaliacao]:
        """Lista avaliações recentes e carrega o autor sem consultas adicionais."""
        return (
            self.db.query(Avaliacao)
            .options(joinedload(Avaliacao.usuario))
            .filter(Avaliacao.hotel_id == hotel_id)
            .order_by(Avaliacao.criado_em.desc())
            .limit(limit)
            .all()
        )

    def list_by_usuario_id(self, usuario_id: uuid.UUID) -> List[Avaliacao]:
        """Lista as avaliações feitas por um usuário, da mais recente à mais antiga."""
        return (
            self.db.query(Avaliacao)
            .filter(Avaliacao.usuario_id == usuario_id)
            .order_by(Avaliacao.criado_em.desc())
            .all()
        )

    def calcular_estatisticas_hotel(self, hotel_id: uuid.UUID) -> Tuple[float, int]:
        """Calcula a média (1 casa decimal) e a quantidade de avaliações do hotel."""
        resultado = (
            self.db.query(
                func.coalesce(func.avg(Avaliacao.nota), 0.0).label("media"),
                func.count(Avaliacao.id).label("total"),
            )
            .filter(Avaliacao.hotel_id == hotel_id)
            .one()
        )
        media = round(float(resultado.media), 1)
        total = int(resultado.total)
        return media, total

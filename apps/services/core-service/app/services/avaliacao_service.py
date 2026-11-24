import logging
import uuid
from datetime import date
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.models.reserva import Reserva
from app.models.usuario import Usuario
from app.repositories.avaliacao_repository import AvaliacaoRepository
from app.repositories.reserva_repository import ReservaRepository
from app.schemas.avaliacao import AvaliacaoCreateSchema, AvaliacaoResponseSchema

logger = logging.getLogger(__name__)


class AvaliacaoService:
    def __init__(self, db: Session, mongo_db: AsyncIOMotorDatabase):
        self.db = db
        self.mongo_db = mongo_db
        self.avaliacao_repo = AvaliacaoRepository(db)
        self.reserva_repo = ReservaRepository(db)

    async def registrar_avaliacao(
        self, payload: AvaliacaoCreateSchema, usuario: Usuario
    ) -> AvaliacaoResponseSchema:
        """
        Executa o registro de avaliação com checagem rigorosa da regra RFO12:
        - Apenas reservas confirmadas com check-out no passado podem ser avaliadas
        - Não permite avaliar reservas de terceiros
        - Impede avaliação em duplicidade
        """
        
        reserva = self.reserva_repo.get_by_id_with_relations(payload.reserva_id)

        if not reserva:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reserva com ID '{payload.reserva_id}' não foi encontrada.",
            )

        if reserva.usuario_id != usuario.id and not usuario.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: Você só pode avaliar estadias das suas próprias reservas.",
            )

        if reserva.status != "Confirmada":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Regra violada (RF012): Apenas reservas com status 'Confirmada' podem ser avaliadas. "
                    f"Status atual da reserva: '{reserva.status}'."
                ),
            )

        hoje = date.today()
        if reserva.checkout >= hoje:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Regra violada (RF012): Apenas estadias concluídas podem ser avaliadas. "
                    f"O check-out desta reserva está previsto para {reserva.checkout.isoformat()} (hoje é {hoje.isoformat()})."
                ),
            )

        avaliacao_existente = self.avaliacao_repo.get_by_reserva_id(reserva.id)
        if avaliacao_existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta estadia já foi avaliada anteriormente. Não são permitidas avaliações duplicadas.",
            )

        if not reserva.quarto or not reserva.quarto.hotel_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Inconsistência de dados: Quarto ou Hotel vinculado à reserva não encontrado.",
            )
        hotel_id = reserva.quarto.hotel_id

        avaliacao = self.avaliacao_repo.create(
            reserva_id=reserva.id,
            hotel_id=hotel_id,
            usuario_id=usuario.id,
            nota=payload.nota,
            comentario=payload.comentario,
        )

        await self._atualizar_media_mongo(hotel_id)

        return AvaliacaoResponseSchema(
            id=avaliacao.id,
            reserva_id=avaliacao.reserva_id,
            hotel_id=avaliacao.hotel_id,
            usuario_id=avaliacao.usuario_id,
            nota=avaliacao.nota,
            comentario=avaliacao.comentario,
            criado_em=avaliacao.criado_em,
            autor={"id": usuario.id, "nome": usuario.nome},
        )

    async def _atualizar_media_mongo(self, hotel_id: uuid.UUID) -> None:
        """ Recalcula a média e atualiza o catálogo desnormalizado no MongoDB """
        try:
            media, total = self.avaliacao_repo.calcular_estatisticas_hotel(hotel_id)
            col = self.mongo_db["catalogo_hoteis"]
            await col.update_one(
                {"_id": str(hotel_id)},
                {"$set": {"media_avaliacoes": media, "total_avaliacoes": total}},
            )
            logger.info(
                f"[CQRS] Catálogo MongoDB atualizado para hotel {hotel_id}: média={media}, total={total}"
            )
        except Exception as e:
            logger.error(f"[CQRS] Erro ao sincronizar média de avaliações no MongoDB: {e}")

    def listar_avaliacoes_hotel(self, hotel_id: uuid.UUID) -> List[AvaliacaoResponseSchema]:
        avaliacoes = self.avaliacao_repo.list_by_hotel_id(hotel_id)
        return [
            AvaliacaoResponseSchema(
                id=a.id,
                reserva_id=a.reserva_id,
                hotel_id=a.hotel_id,
                usuario_id=a.usuario_id,
                nota=a.nota,
                comentario=a.comentario,
                criado_em=a.criado_em,
                autor={"id": a.usuario.id, "nome": a.usuario.nome} if a.usuario else None,
            )
            for a in avaliacoes
        ]
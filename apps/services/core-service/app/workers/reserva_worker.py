import asyncio
import json
import logging
import uuid
from datetime import date, datetime

import aio_pika
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.mongodb import get_mongo_db
from app.models.reserva import Reserva
from app.repositories.reserva_repository import ReservaRepository

logging.basicConfig(level=logging.INFO, format="[ReservaWorker] %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("reserva_worker")

FILA_SOLICITACOES = "solicitacoes-reserva"


async def processar_mensagem(message: aio_pika.IncomingMessage):
    async with message.process():
        corpo = json.loads(message.body.decode())
        reserva_id = uuid.UUID(corpo["reserva_id"])
        usuario_id = corpo.get("usuario_id")
        quarto_id = uuid.UUID(corpo["quarto_id"])
        checkin = date.fromisoformat(corpo["checkin"])
        checkout = date.fromisoformat(corpo["checkout"])
        valor_total = float(corpo["valor_total"])

        logger.info(f"Processando reserva {reserva_id} (Usuário: {usuario_id}) para Quarto {quarto_id}")

        db: Session = SessionLocal()
        try:
            repo = ReservaRepository(db)
            reserva: Reserva = repo.get_by_id(reserva_id)
            if not reserva:
                logger.error(f"Reserva {reserva_id} não encontrada no banco.")
                return

            conflitos = repo.list_conflitos(quarto_id, checkin, checkout)
            if conflitos:
                logger.warning(f"Overbooking detectado para a reserva {reserva_id}. Cancelando.")
                repo.update_status(reserva, "Cancelada")
                motivo = "Overbooking: quarto indisponível no período solicitado."
                status_final = "Cancelada"
            else:
                logger.info(f"Simulando confirmação de pagamento para reserva {reserva_id}...")
                await asyncio.sleep(2.0)
                repo.update_status(reserva, "Confirmada")
                motivo = "Pagamento aprovado e reserva confirmada com sucesso."
                status_final = "Confirmada"

            mongo_db = get_mongo_db()
            auditoria = {
                "reserva_id": str(reserva_id),
                "usuario_id": str(usuario_id),
                "quarto_id": str(quarto_id),
                "checkin": checkin.isoformat(),
                "checkout": checkout.isoformat(),
                "valor_total": valor_total,
                "status": status_final,
                "motivo": motivo,
                "processado_em": datetime.utcnow().isoformat(),
            }
            await mongo_db.historico_auditoria.insert_one(auditoria)
            logger.info(f"Auditoria gravada no MongoDB para reserva {reserva_id} ({status_final})")

        except Exception as e:
            logger.exception(f"Erro inesperado ao processar reserva {reserva_id}: {e}")
        finally:
            db.close()


async def main():
    logger.info("Iniciando Worker de Reservas Assíncronas (Sprint 7)...")
    conexao = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    canal = await conexao.channel()
    await canal.set_qos(prefetch_count=1)

    fila = await canal.declare_queue(FILA_SOLICITACOES, durable=True)
    logger.info(f"Aguardando mensagens na fila '{FILA_SOLICITACOES}' (consumo serial prefetch=1)...")
    await fila.consume(processar_mensagem)
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
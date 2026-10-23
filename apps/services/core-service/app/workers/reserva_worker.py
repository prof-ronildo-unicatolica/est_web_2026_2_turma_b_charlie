import asyncio
import json
import uuid
from datetime import date, datetime

import aio_pika
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.reserva_repository import ReservaRepository

FILA_SOLICITACOES = "solicitacoes-reserva"


async def _gravar_auditoria(mongo_db, reserva_id, quarto_id, status_final, motivo, checkin, checkout, valor_total):
    await mongo_db["historico_auditoria"].insert_one({
        "reserva_id": reserva_id, "quarto_id": quarto_id,
        "status_final": status_final, "motivo": motivo,
        "checkin": checkin, "checkout": checkout,
        "valor_total": valor_total, "processado_em": datetime.utcnow().isoformat(),
    })
    print(f"[Worker] Auditoria: reserva={reserva_id} status={status_final}")


async def _processar_mensagem(message: aio_pika.IncomingMessage, mongo_db):
    async with message.process():
        db = SessionLocal()
        try:
            data = json.loads(message.body.decode("utf-8"))
            reserva_id = uuid.UUID(data["reserva_id"])
            checkin = date.fromisoformat(data["checkin"])
            checkout = date.fromisoformat(data["checkout"])

            print(f"[Worker] Processando {data['reserva_id']} | quarto={data['quarto_id']}")

            repo = ReservaRepository(db)
            reserva = repo.get_by_id(reserva_id)
            if not reserva:
                print(f"[Worker] Reserva não encontrada. Descartando.")
                return

            
            conflitos = repo.list_conflitos(reserva.quarto_id, checkin, checkout)
            if conflitos:
                motivo = f"Overbooking: {len(conflitos)} reserva(s) confirmada(s) no período."
                repo.update_status(reserva, "Cancelada")
                print(f"[Worker] CANCELADA — {motivo}")
                await _gravar_auditoria(mongo_db, data["reserva_id"], data["quarto_id"],
                                        "Cancelada", motivo, data["checkin"], data["checkout"],
                                        float(data["valor_total"]))
                return

            
            print(f"[Worker] Simulando pagamento...")
            await asyncio.sleep(2)

           
            repo.update_status(reserva, "Confirmada")
            print(f"[Worker] CONFIRMADA!")
            await _gravar_auditoria(mongo_db, data["reserva_id"], data["quarto_id"],
                                    "Confirmada", "Pagamento aprovado. Sem overbooking.",
                                    data["checkin"], data["checkout"], float(data["valor_total"]))

        except Exception as exc:
            print(f"[Worker] ERRO: {exc}")
            try:
                repo = ReservaRepository(db)
                r = repo.get_by_id(uuid.UUID(json.loads(message.body.decode())["reserva_id"]))
                if r and r.status == "Pendente":
                    repo.update_status(r, "Cancelada")
            except Exception:
                pass
        finally:
            db.close()


async def main():
    print(f"[Worker] Conectando ao RabbitMQ: {settings.RABBITMQ_URL}")
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    mongo_client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongo_db = mongo_client[settings.MONGODB_DB]

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)  
        queue = await channel.declare_queue(FILA_SOLICITACOES, durable=True)
        print(f"[Worker] Aguardando '{FILA_SOLICITACOES}' (prefetch=1, serial)")
        await queue.consume(lambda msg: _processar_mensagem(msg, mongo_db))
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[Worker] Parado.")
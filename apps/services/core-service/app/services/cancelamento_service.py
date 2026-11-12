import logging
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.models.reserva import Reserva

logger = logging.getLogger(__name__)

HORA_PADRAO_CHECKIN = time(14, 0)


class CancelamentoService:
    """Calcula as políticas de cancelamento e registra auditoria (RFO10/RFO11)."""

    def __init__(self, db: Session, mongo_db: AsyncIOMotorDatabase):
        self.db = db
        self.mongo_db = mongo_db

    @staticmethod
    def calcular_limite_cancelamento(checkin: date) -> datetime:
        """Limite de cancelamento gratuito: 48h antes das 14h do check-in."""
        dt_checkin = datetime.combine(checkin, HORA_PADRAO_CHECKIN)
        return dt_checkin - timedelta(hours=48)

    @staticmethod
    def extrair_valor_uma_diaria(reserva: Reserva) -> float:
        """Obtém uma diária do snapshot, do quarto ou, por último, do total dividido."""
        snapshot = reserva.cotacao_snapshot
        if isinstance(snapshot, dict):
            diarias = snapshot.get("diarias")
            if isinstance(diarias, list) and diarias:
                primeira_diaria = diarias[0]
                if isinstance(primeira_diaria, dict):
                    valor_final = primeira_diaria.get("valor_final")
                    try:
                        if valor_final is not None and float(valor_final) >= 0:
                            return float(valor_final)
                    except (TypeError, ValueError):
                        # Snapshot inválido: tenta o preço do quarto e depois o fallback.
                        pass

        quarto = getattr(reserva, "quarto", None)
        preco_diaria = getattr(quarto, "preco_diaria", None)
        try:
            if preco_diaria is not None and float(preco_diaria) > 0:
                return float(preco_diaria)
        except (TypeError, ValueError):
            pass

        numero_dias = max((reserva.checkout - reserva.checkin).days, 1)
        return round(float(reserva.valor_total) / numero_dias, 2)

    def calcular_politica(
        self,
        reserva: Reserva,
        data_referencia: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Aplica os quatro cenários de cancelamento definidos pela regra de 48h."""
        agora = data_referencia if data_referencia is not None else datetime.utcnow()
        dt_checkin = datetime.combine(reserva.checkin, HORA_PADRAO_CHECKIN)
        data_limite = self.calcular_limite_cancelamento(reserva.checkin)

        horas_ate_checkin = (dt_checkin - agora).total_seconds() / 3600.0
        dentro_do_prazo = agora <= data_limite
        tipo_tarifa = (reserva.tipo_tarifa or "reembolsavel").strip().lower()
        valor_total = float(reserva.valor_total)

        if tipo_tarifa == "reembolsavel":
            if dentro_do_prazo:
                cenario = "Cenário 1: Reembolsável Antecipado (>= 48h)"
                valor_multa = 0.0
                valor_reembolso = valor_total
                mensagem = (
                    "Cancelamento gratuito realizado dentro do prazo de 48h. "
                    "Reembolso integral concedido."
                )
            else:
                cenario = "Cenário 2: Reembolsável Tardio (< 48h)"
                valor_uma_diaria = self.extrair_valor_uma_diaria(reserva)
                valor_multa = round(min(valor_uma_diaria, valor_total), 2)
                valor_reembolso = round(max(valor_total - valor_multa, 0.0), 2)
                mensagem = (
                    f"Cancelamento tardio (< 48h). Retenção de 1 diária de multa "
                    f"(R$ {valor_multa:.2f})."
                )
        else:
            if dentro_do_prazo:
                cenario = "Cenário 3: Não-Reembolsável Antecipado (>= 48h)"
                mensagem = (
                    "Tarifa Não-Reembolsável: cancelamento com retenção integral "
                    "(100% de multa)."
                )
            else:
                cenario = "Cenário 4: Não-Reembolsável Tardio (< 48h)"
                mensagem = (
                    "Tarifa Não-Reembolsável: cancelamento tardio com retenção "
                    "integral (100% de multa)."
                )
            valor_multa = valor_total
            valor_reembolso = 0.0

        return {
            "reserva_id": reserva.id,
            "tipo_tarifa": tipo_tarifa,
            "checkin": reserva.checkin,
            "data_limite_cancelamento": data_limite,
            "dentro_do_prazo": dentro_do_prazo,
            "horas_ate_checkin": round(horas_ate_checkin, 2),
            "valor_total": valor_total,
            "valor_multa": valor_multa,
            "valor_reembolso": valor_reembolso,
            "cenario_identificado": cenario,
            "mensagem_politica": mensagem,
        }

    async def registrar_auditoria_cancelamento(
        self,
        reserva: Reserva,
        resultado_politica: Dict[str, Any],
        motivo_usuario: Optional[str] = None,
    ) -> None:
        """Registra o evento de cancelamento na coleção MongoDB historico_auditoria."""
        try:
            quarto = getattr(reserva, "quarto", None)
            documento = {
                "tipo_evento": "CANCELAMENTO_RESERVA",
                "reserva_id": str(reserva.id),
                "usuario_id": str(reserva.usuario_id),
                "quarto_id": str(reserva.quarto_id),
                "hotel_id": str(quarto.hotel_id) if quarto else None,
                "checkin": reserva.checkin.isoformat(),
                "checkout": reserva.checkout.isoformat(),
                "tipo_tarifa": resultado_politica["tipo_tarifa"],
                "cenario": resultado_politica["cenario_identificado"],
                "dentro_do_prazo_48h": resultado_politica["dentro_do_prazo"],
                "horas_ate_checkin": resultado_politica["horas_ate_checkin"],
                "valor_total_reserva": resultado_politica["valor_total"],
                "valor_multa": resultado_politica["valor_multa"],
                "valor_reembolso": resultado_politica["valor_reembolso"],
                "motivo_usuario": motivo_usuario,
                "data_cancelamento": datetime.utcnow().isoformat(),
            }
            await self.mongo_db["historico_auditoria"].insert_one(documento)
            logger.info(
                "Cancelamento registrado para reserva %s; multa: R$ %.2f",
                reserva.id,
                resultado_politica["valor_multa"],
            )
        except Exception:
            # A auditoria falha sem desfazer o cancelamento já persistido no PostgreSQL.
            logger.exception(
                "Falha ao registrar auditoria do cancelamento da reserva %s",
                getattr(reserva, "id", "desconhecida"),
            )

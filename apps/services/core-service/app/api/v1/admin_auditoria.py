from asyncio import gather
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_admin
from app.core.database import get_mongo_db
from app.models.usuario import Usuario

router = APIRouter(prefix="/admin/auditoria", tags=["Admin — Auditoria (UC11)"])


@router.get(
    "",
    summary="[ADMIN] Consulta a trilha de auditoria e logs operacionais do MongoDB",
)
async def listar_logs_auditoria(
    tipo_evento: Optional[str] = Query(default=None, description="Filtrar por tipo de evento"),
    reserva_id: Optional[str] = Query(default=None, description="Filtrar por ID da reserva"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    filtro: Dict[str, Any] = {}
    if tipo_evento:
        filtro["tipo_evento"] = tipo_evento
    if reserva_id:
        filtro["reserva_id"] = reserva_id

    pipeline = [
        {"$match": filtro},
        {
            "$unionWith": {
                "coll": "logs_auditoria",
                "pipeline": [{"$match": filtro}],
            }
        },
        {
            "$facet": {
                "items": [
                    {"$sort": {"_id": -1}},
                    {"$skip": offset},
                    {"$limit": limit},
                ],
                "total": [{"$count": "value"}],
            }
        },
    ]
    resultados = await mongo_db["historico_auditoria"].aggregate(pipeline).to_list(length=1)
    resultado = resultados[0] if resultados else {"items": [], "total": []}
    items = resultado["items"]
    for doc in items:
        doc["id"] = str(doc.pop("_id"))

    return {
        "items": items,
        "total": resultado["total"][0]["value"] if resultado["total"] else 0,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/tipos-eventos",
    summary="[ADMIN] Retorna os tipos distintos de eventos registrados na auditoria",
)
async def listar_tipos_eventos(
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    _admin: Usuario = Depends(get_current_admin),
):
    historico, logs = await gather(
        mongo_db["historico_auditoria"].distinct("tipo_evento"),
        mongo_db["logs_auditoria"].distinct("tipo_evento"),
    )
    return sorted({tipo for tipo in historico + logs if isinstance(tipo, str) and tipo})

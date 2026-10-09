from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.core.database import get_db, get_mongo_db
from app.schemas.hotel import BuscaCatalogoResponseSchema, CatalogoHotelItemSchema
from app.services.catalogo_mongo_service import CatalogoMongoService

router = APIRouter(tags=["Busca Pública"])


@router.get(
    "/busca",
    response_model=BuscaCatalogoResponseSchema,
    summary="Busca pública de hotéis via MongoDB (RFO04 & Bônus RFO05)",
)
async def buscar_hoteis_catalogo(
    cidade: Optional[str] = Query(default=None, description="Nome da cidade (parcial ou exato)"),
    cidade_id: Optional[str] = Query(default=None, description="UUID da cidade"),
    estrelas: Optional[int] = Query(default=None, ge=1, le=5, description="Categoria mínima de estrelas"),
    adultos: Optional[int] = Query(default=None, ge=1, description="Mínimo de adultos por quarto"),
    criancas: Optional[int] = Query(default=None, ge=0, description="Mínimo de crianças por quarto"),
    preco_max: Optional[float] = Query(default=None, gt=0, description="Preço máximo da diária"),
    lat: Optional[float] = Query(default=None, description="Latitude para filtro territorial (RFO05)"),
    lng: Optional[float] = Query(default=None, description="Longitude para filtro territorial (RFO05)"),
    db: Session = Depends(get_db),
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    service = CatalogoMongoService(mongo_db, db)
    docs = await service.buscar(
        cidade=cidade,
        cidade_id=cidade_id,
        estrelas=estrelas,
        adultos=adultos,
        criancas=criancas,
        preco_max=preco_max,
        lat=lat,
        lng=lng,
    )

    itens = [
        CatalogoHotelItemSchema(
            hotel_id=doc["hotel_id"],
            nome=doc["nome"],
            categoria_estrelas=doc.get("categoria_estrelas"),
            cidade_nome=doc["cidade"]["nome"],
            cidade_id=doc["cidade"]["id"],
            comodidades=doc.get("comodidades", []),
            preco_minimo=doc.get("preco_minimo", 0.0),
            capacidade_maxima_adultos=doc.get("capacidade_maxima_adultos", 0),
            capacidade_maxima_criancas=doc.get("capacidade_maxima_criancas", 0),
            total_quartos_ativos=doc.get("total_quartos_ativos", 0),
            quartos_disponiveis=doc.get("quartos", []),
        )
        for doc in docs
    ]

    filtros = {
        "cidade": cidade,
        "estrelas": estrelas,
        "adultos": adultos,
        "criancas": criancas,
        "preco_max": preco_max,
        "coordenadas": {"lat": lat, "lng": lng} if (lat and lng) else None,
    }

    return BuscaCatalogoResponseSchema(
        total=len(itens),
        filtros_aplicados=filtros,
        hoteis=itens,
    )
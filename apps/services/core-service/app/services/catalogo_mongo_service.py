import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.models.hotel import Hotel
from app.repositories.hotel_repository import HotelRepository

logger = logging.getLogger(__name__)


class CatalogoMongoService:
    """Gerencia a coleção desnormalizada 'catalogo_hoteis' no MongoDB (CQRS Read Model)."""

    COLECAO = "catalogo_hoteis"

    def __init__(self, mongo_db: AsyncIOMotorDatabase, db: Session):
        self.mongo_db = mongo_db
        self.db = db
        self.hotel_repo = HotelRepository(db)

    async def inicializar_indices(self) -> None:
        """Cria índices para acelerar filtros de busca e suportar consultas espaciais GeoJSON."""
        col = self.mongo_db[self.COLECAO]
        try:
            await col.create_index("cidade.nome")
            await col.create_index("cidade.id")
            await col.create_index("categoria_estrelas")
            await col.create_index("preco_minimo")
            await col.create_index("quartos.max_adultos")
            await col.create_index("quartos.max_criancas")
            # Índice espacial para o Bônus RFO05 (filtro territorial via GeoJSON)
            await col.create_index([("cidade.limite_territorial", "2dsphere")])
            logger.info("Índices da coleção 'catalogo_hoteis' garantidos com sucesso.")
        except Exception as e:
            logger.warning(f"Aviso ao inicializar índices do MongoDB: {e}")

    def _montar_documento(self, hotel: Hotel) -> Dict[str, Any]:
        """Converte a entidade relacional rica em documento desnormalizado para o MongoDB."""
        quartos_ativos = [q for q in hotel.quartos if q.ativo]
        precos = [q.preco_diaria for q in quartos_ativos]
        preco_minimo = min(precos) if precos else 0.0

        max_adultos = max([q.max_adultos for q in quartos_ativos]) if quartos_ativos else 0
        max_criancas = max([q.max_criancas for q in quartos_ativos]) if quartos_ativos else 0

        # Sanitiza GeoJSON para o padrão MongoDB
        limite = hotel.cidade.limite_territorial
        if isinstance(limite, dict) and "type" in limite and "coordinates" in limite:
            limite_geojson = limite
        else:
            limite_geojson = None

        return {
            "_id": str(hotel.id),
            "hotel_id": str(hotel.id),
            "nome": hotel.nome,
            "categoria_estrelas": hotel.categoria_estrelas,
            "cidade": {
                "id": str(hotel.cidade.id),
                "nome": hotel.cidade.nome,
                "limite_territorial": limite_geojson,
            },
            "comodidades": [c.nome for c in hotel.comodidades],
            "preco_minimo": float(preco_minimo),
            "capacidade_maxima_adultos": max_adultos,
            "capacidade_maxima_criancas": max_criancas,
            "total_quartos_ativos": len(quartos_ativos),
            "quartos": [
                {
                    "id": str(q.id),
                    "numero": q.numero,
                    "tipo": q.tipo,
                    "preco_diaria": float(q.preco_diaria),
                    "max_adultos": q.max_adultos,
                    "max_criancas": q.max_criancas,
                    "descricao": q.descricao,
                    "ativo": q.ativo,
                }
                for q in hotel.quartos
            ],
            "atualizado_em": datetime.now(timezone.utc).isoformat(),
        }

    async def sincronizar_hotel(self, hotel_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Lê o hotel do PostgreSQL e realiza UPSERT na coleção do MongoDB."""
        hotel = self.hotel_repo.get_by_id(hotel_id)
        col = self.mongo_db[self.COLECAO]

        if not hotel:
            await col.delete_one({"_id": str(hotel_id)})
            logger.info(f"Hotel '{hotel_id}' removido da projeção do MongoDB.")
            return None

        doc = self._montar_documento(hotel)
        await col.replace_one({"_id": str(hotel.id)}, doc, upsert=True)
        logger.info(f"Hotel '{hotel.nome}' sincronizado na projeção do MongoDB.")
        return doc

    async def remover_hotel(self, hotel_id: uuid.UUID) -> None:
        """Remove o documento do hotel do MongoDB quando deletado do PostgreSQL."""
        col = self.mongo_db[self.COLECAO]
        await col.delete_one({"_id": str(hotel_id)})

    async def reconstruir_todo_catalogo(self) -> int:
        """Recria toda a projeção no MongoDB a partir dos dados do PostgreSQL."""
        hoteis = self.hotel_repo.list()
        count = 0
        for h in hoteis:
            await self.sincronizar_hotel(h.id)
            count += 1
        return count

    async def buscar(
        self,
        cidade: Optional[str] = None,
        cidade_id: Optional[str] = None,
        estrelas: Optional[int] = None,
        adultos: Optional[int] = None,
        criancas: Optional[int] = None,
        preco_max: Optional[float] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca pública (RFO04) e opcionalmente o filtro territorial (RFO05)
        diretamente no MongoDB.
        """
        query: Dict[str, Any] = {}

        
        if cidade:
            query["cidade.nome"] = {"$regex": cidade.strip(), "$options": "i"}

        if cidade_id:
            query["cidade.id"] = cidade_id

        
        if estrelas is not None:
            query["categoria_estrelas"] = {"$gte": estrelas}

        
        elem_match: Dict[str, Any] = {"ativo": True}
        if adultos is not None and adultos > 0:
            elem_match["max_adultos"] = {"$gte": adultos}
        if criancas is not None and criancas > 0:
            elem_match["max_criancas"] = {"$gte": criancas}

        if len(elem_match) > 1:
            query["quartos"] = {"$elemMatch": elem_match}

        
        if preco_max is not None and preco_max > 0:
            query["preco_minimo"] = {"$lte": preco_max}

        
        if lat is not None and lng is not None:
            query["cidade.limite_territorial"] = {
                "$geoIntersects": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [float(lng), float(lat)],
                    }
                }
            }

        col = self.mongo_db[self.COLECAO]
        cursor = col.find(query).sort("preco_minimo", 1)
        docs = await cursor.to_list(length=100)
        return docs

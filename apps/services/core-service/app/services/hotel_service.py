import uuid
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.models.hotel import Cidade, Comodidade, Hotel, Quarto
from app.repositories.hotel_repository import (
    CidadeRepository,
    ComodidadeRepository,
    HotelRepository,
    QuartoRepository,
)
from app.services.catalogo_mongo_service import CatalogoMongoService



class RegraDeNegocioError(Exception):
    """Base para erros de negócio do domínio."""


class CidadeJaExisteError(RegraDeNegocioError):
    pass


class CidadeNaoEncontradaError(RegraDeNegocioError):
    pass


class HotelNaoEncontradoError(RegraDeNegocioError):
    pass


class ComodidadeJaExisteError(RegraDeNegocioError):
    pass


class ComodidadeNaoEncontradaError(RegraDeNegocioError):
    pass


class QuartoNaoEncontradoError(RegraDeNegocioError):
    pass


class QuartoNumeroDuplicadoError(RegraDeNegocioError):
    pass


class CapacidadeInvalidaError(RegraDeNegocioError):
    pass



class ComodidadeService:
    def __init__(self, db: Session):
        self.repo = ComodidadeRepository(db)

    def criar(self, nome: str) -> Comodidade:
        nome = nome.strip()
        if self.repo.get_by_nome(nome):
            raise ComodidadeJaExisteError(f"Já existe uma comodidade chamada '{nome}'.")
        return self.repo.create(nome=nome)

    def listar(self) -> List[Comodidade]:
        return self.repo.list()

    def buscar_por_id(self, comodidade_id: uuid.UUID) -> Comodidade:
        comodidade = self.repo.get_by_id(comodidade_id)
        if not comodidade:
            raise ComodidadeNaoEncontradaError(f"Comodidade '{comodidade_id}' não encontrada.")
        return comodidade

    def atualizar(self, comodidade_id: uuid.UUID, nome: str) -> Comodidade:
        comodidade = self.buscar_por_id(comodidade_id)
        nome = nome.strip()
        existente = self.repo.get_by_nome(nome)
        if existente and existente.id != comodidade_id:
            raise ComodidadeJaExisteError(f"Já existe uma comodidade chamada '{nome}'.")
        return self.repo.update(comodidade, nome=nome)

    def remover(self, comodidade_id: uuid.UUID) -> None:
        comodidade = self.buscar_por_id(comodidade_id)
        self.repo.delete(comodidade)



class CidadeService:
    def __init__(self, db: Session):
        self.repository = CidadeRepository(db)

    def criar(self, nome: str, limite_territorial: dict | None = None) -> Cidade:
        nome = nome.strip()
        if self.repository.get_by_nome(nome):
            raise CidadeJaExisteError(f"Já existe uma cidade chamada '{nome}'.")
        return self.repository.create(nome=nome, limite_territorial=limite_territorial)

    def listar(self) -> List[Cidade]:
        return self.repository.list()

    def buscar_por_id(self, cidade_id: uuid.UUID) -> Cidade:
        cidade = self.repository.get_by_id(cidade_id)
        if not cidade:
            raise CidadeNaoEncontradaError(f"Cidade '{cidade_id}' não encontrada.")
        return cidade

    def atualizar(self, cidade_id: uuid.UUID, dados: dict) -> Cidade:
        cidade = self.buscar_por_id(cidade_id)
        novo_nome = dados.get("nome")
        if novo_nome:
            novo_nome = novo_nome.strip()
            existente = self.repository.get_by_nome(novo_nome)
            if existente and existente.id != cidade_id:
                raise CidadeJaExisteError(f"Já existe uma cidade chamada '{novo_nome}'.")
            dados["nome"] = novo_nome

        dados_filtrados = {
            k: v for k, v in dados.items()
            if v is not None or k == "limite_territorial"
        }
        return self.repository.update(cidade, dados_filtrados)

    def remover(self, cidade_id: uuid.UUID) -> None:
        cidade = self.buscar_por_id(cidade_id)
        self.repository.delete(cidade)



class HotelService:
    def __init__(self, db: Session, mongo_db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.repository = HotelRepository(db)
        self.cidades = CidadeRepository(db)
        self.comodidades = ComodidadeRepository(db)
        self.mongo_service = CatalogoMongoService(mongo_db, db) if mongo_db is not None else None

    async def criar(
        self,
        nome: str,
        cidade_id: uuid.UUID,
        categoria_estrelas: int | None = None,
    ) -> Hotel:
        nome = nome.strip()
        if not self.cidades.get_by_id(cidade_id):
            raise CidadeNaoEncontradaError(f"Não existe cidade com id '{cidade_id}'.")
        hotel = self.repository.create(
            nome=nome,
            cidade_id=cidade_id,
            categoria_estrelas=categoria_estrelas,
        )
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(hotel.id)
        return hotel

    def listar(self, cidade_id: uuid.UUID | None = None) -> List[Hotel]:
        if cidade_id is not None:
            if not self.cidades.get_by_id(cidade_id):
                raise CidadeNaoEncontradaError(f"Não existe cidade com id '{cidade_id}'.")
            return self.repository.list_by_cidade(cidade_id)
        return self.repository.list()

    def buscar_por_id(self, hotel_id: uuid.UUID) -> Hotel:
        hotel = self.repository.get_by_id(hotel_id)
        if not hotel:
            raise HotelNaoEncontradoError(f"Hotel '{hotel_id}' não encontrado.")
        return hotel

    async def atualizar(self, hotel_id: uuid.UUID, dados: dict) -> Hotel:
        hotel = self.buscar_por_id(hotel_id)
        cidade_id = dados.get("cidade_id")
        if cidade_id and not self.cidades.get_by_id(cidade_id):
            raise CidadeNaoEncontradaError(f"Não existe cidade com id '{cidade_id}'.")
        dados_filtrados = {k: v for k, v in dados.items() if v is not None}
        hotel_atualizado = self.repository.update(hotel, dados_filtrados)
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(hotel_atualizado.id)
        return hotel_atualizado

    async def remover(self, hotel_id: uuid.UUID) -> None:
        hotel = self.buscar_por_id(hotel_id)
        self.repository.delete(hotel)
        if self.mongo_service:
            await self.mongo_service.remover_hotel(hotel_id)

    async def adicionar_comodidade(
        self, hotel_id: uuid.UUID, comodidade_id: uuid.UUID
    ) -> Hotel:
        hotel = self.buscar_por_id(hotel_id)
        comodidade = self.comodidades.get_by_id(comodidade_id)
        if not comodidade:
            raise ComodidadeNaoEncontradaError(f"Comodidade '{comodidade_id}' não encontrada.")
        hotel_atualizado = self.repository.adicionar_comodidade(hotel, comodidade)
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(hotel.id)
        return hotel_atualizado

    async def remover_comodidade(
        self, hotel_id: uuid.UUID, comodidade_id: uuid.UUID
    ) -> Hotel:
        hotel = self.buscar_por_id(hotel_id)
        comodidade = self.comodidades.get_by_id(comodidade_id)
        if not comodidade:
            raise ComodidadeNaoEncontradaError(f"Comodidade '{comodidade_id}' não encontrada.")
        hotel_atualizado = self.repository.remover_comodidade(hotel, comodidade)
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(hotel.id)
        return hotel_atualizado



class QuartoService:
    def __init__(self, db: Session, mongo_db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self.repo = QuartoRepository(db)
        self.hotel_repo = HotelRepository(db)
        self.mongo_service = CatalogoMongoService(mongo_db, db) if mongo_db is not None else None

    async def criar(
        self,
        hotel_id: uuid.UUID,
        numero: str,
        tipo: str,
        preco_diaria: float,
        max_adultos: int = 2,
        max_criancas: int = 0,
        descricao: str | None = None,
        ativo: bool = True,
    ) -> Quarto:
        numero = numero.strip()
        tipo = tipo.strip()

        
        if not self.hotel_repo.get_by_id(hotel_id):
            raise HotelNaoEncontradoError(f"Não existe hotel com id '{hotel_id}'.")

       
        if self.repo.get_by_numero(hotel_id, numero):
            raise QuartoNumeroDuplicadoError(
                f"O quarto número '{numero}' já está cadastrado neste hotel."
            )

        
        if max_adultos < 1:
            raise CapacidadeInvalidaError("A capacidade de adultos deve ser no mínimo 1.")
        if max_criancas < 0:
            raise CapacidadeInvalidaError("A capacidade de crianças não pode ser negativa.")

        quarto = self.repo.create(
            hotel_id=hotel_id,
            numero=numero,
            tipo=tipo,
            preco_diaria=preco_diaria,
            max_adultos=max_adultos,
            max_criancas=max_criancas,
            descricao=descricao,
            ativo=ativo,
        )

        
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(hotel_id)

        return quarto

    def listar_por_hotel(self, hotel_id: uuid.UUID) -> List[Quarto]:
        if not self.hotel_repo.get_by_id(hotel_id):
            raise HotelNaoEncontradoError(f"Não existe hotel com id '{hotel_id}'.")
        return self.repo.list_by_hotel(hotel_id)

    def listar_todos(self) -> List[Quarto]:
        return self.repo.list_all()

    def buscar_por_id(self, quarto_id: uuid.UUID) -> Quarto:
        quarto = self.repo.get_by_id(quarto_id)
        if not quarto:
            raise QuartoNaoEncontradoError(f"Quarto '{quarto_id}' não encontrado.")
        return quarto

    async def atualizar(self, quarto_id: uuid.UUID, dados: dict) -> Quarto:
        quarto = self.buscar_por_id(quarto_id)
        novo_numero = dados.get("numero")

        if novo_numero:
            novo_numero = novo_numero.strip()
            existente = self.repo.get_by_numero(quarto.hotel_id, novo_numero)
            if existente and existente.id != quarto_id:
                raise QuartoNumeroDuplicadoError(
                    f"O quarto número '{novo_numero}' já existe neste hotel."
                )
            dados["numero"] = novo_numero

        if "max_adultos" in dados and dados["max_adultos"] is not None and dados["max_adultos"] < 1:
            raise CapacidadeInvalidaError("A capacidade de adultos deve ser no mínimo 1.")

        if "max_criancas" in dados and dados["max_criancas"] is not None and dados["max_criancas"] < 0:
            raise CapacidadeInvalidaError("A capacidade de crianças não pode ser negativa.")

        dados_filtrados = {k: v for k, v in dados.items() if v is not None}
        quarto_atualizado = self.repo.update(quarto, dados_filtrados)

       
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(quarto_atualizado.hotel_id)

        return quarto_atualizado

    async def remover(self, quarto_id: uuid.UUID) -> None:
        quarto = self.buscar_por_id(quarto_id)
        hotel_id = quarto.hotel_id
        self.repo.delete(quarto)

    
        if self.mongo_service:
            await self.mongo_service.sincronizar_hotel(hotel_id)
```
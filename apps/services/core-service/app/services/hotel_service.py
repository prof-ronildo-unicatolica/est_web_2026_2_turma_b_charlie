import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.hotel import Cidade, Comodidade, Hotel
from app.repositories.hotel_repository import (
    CidadeRepository,
    ComodidadeRepository,
    HotelRepository,
)


# ─── Exceções de Domínio ─────────────────────────────────────────────────────

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
            raise ComodidadeNaoEncontradaError(
                f"Comodidade '{comodidade_id}' não encontrada."
            )
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
        # Mantém 'limite_territorial' mesmo se None (permite limpar o campo)
        dados_filtrados = {
            k: v for k, v in dados.items()
            if v is not None or k == "limite_territorial"
        }
        return self.repository.update(cidade, dados_filtrados)

    def remover(self, cidade_id: uuid.UUID) -> None:
        cidade = self.buscar_por_id(cidade_id)
        self.repository.delete(cidade)



class HotelService:
    def __init__(self, db: Session):
        self.repository = HotelRepository(db)
        self.cidades = CidadeRepository(db)
        self.comodidades = ComodidadeRepository(db)

    def criar(
        self,
        nome: str,
        cidade_id: uuid.UUID,
        categoria_estrelas: int | None = None,
    ) -> Hotel:
        nome = nome.strip()
        if not self.cidades.get_by_id(cidade_id):
            raise CidadeNaoEncontradaError(f"Não existe cidade com id '{cidade_id}'.")
        return self.repository.create(
            nome=nome,
            cidade_id=cidade_id,
            categoria_estrelas=categoria_estrelas,
        )

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

    def atualizar(self, hotel_id: uuid.UUID, dados: dict) -> Hotel:
        hotel = self.buscar_por_id(hotel_id)
        cidade_id = dados.get("cidade_id")
        if cidade_id and not self.cidades.get_by_id(cidade_id):
            raise CidadeNaoEncontradaError(f"Não existe cidade com id '{cidade_id}'.")
        dados_filtrados = {k: v for k, v in dados.items() if v is not None}
        return self.repository.update(hotel, dados_filtrados)

    def remover(self, hotel_id: uuid.UUID) -> None:
        hotel = self.buscar_por_id(hotel_id)
        self.repository.delete(hotel)

    def adicionar_comodidade(
        self, hotel_id: uuid.UUID, comodidade_id: uuid.UUID
    ) -> Hotel:
        hotel = self.buscar_por_id(hotel_id)
        comodidade = self.comodidades.get_by_id(comodidade_id)
        if not comodidade:
            raise ComodidadeNaoEncontradaError(
                f"Comodidade '{comodidade_id}' não encontrada."
            )
        return self.repository.adicionar_comodidade(hotel, comodidade)

    def remover_comodidade(
        self, hotel_id: uuid.UUID, comodidade_id: uuid.UUID
    ) -> Hotel:
        hotel = self.buscar_por_id(hotel_id)
        comodidade = self.comodidades.get_by_id(comodidade_id)
        if not comodidade:
            raise ComodidadeNaoEncontradaError(
                f"Comodidade '{comodidade_id}' não encontrada."
            )
        return self.repository.remover_comodidade(hotel, comodidade)
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.hotel import Cidade, Comodidade, Hotel


# repository: comodidade

class ComodidadeRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, nome: str) -> Comodidade:
        comodidade = Comodidade(nome=nome)
        self.db.add(comodidade)
        self.db.commit()
        self.db.refresh(comodidade)
        return comodidade

    def list(self) -> List[Comodidade]:
        return self.db.query(Comodidade).order_by(Comodidade.nome).all()

    def get_by_id(self, comodidade_id: uuid.UUID) -> Optional[Comodidade]:
        return self.db.query(Comodidade).filter(Comodidade.id == comodidade_id).first()

    def get_by_nome(self, nome: str) -> Optional[Comodidade]:
        return self.db.query(Comodidade).filter(Comodidade.nome == nome).first()

    def update(self, comodidade: Comodidade, nome: str) -> Comodidade:
        comodidade.nome = nome
        self.db.commit()
        self.db.refresh(comodidade)
        return comodidade

    def delete(self, comodidade: Comodidade) -> None:
        self.db.delete(comodidade)
        self.db.commit()


# repository: cidade

class CidadeRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, nome: str, limite_territorial: dict | None = None) -> Cidade:
        cidade = Cidade(nome=nome, limite_territorial=limite_territorial)
        self.db.add(cidade)
        self.db.commit()
        self.db.refresh(cidade)
        return cidade

    def list(self) -> List[Cidade]:
        return self.db.query(Cidade).order_by(Cidade.nome).all()

    def get_by_id(self, cidade_id: uuid.UUID) -> Optional[Cidade]:
        return self.db.query(Cidade).filter(Cidade.id == cidade_id).first()

    def get_by_nome(self, nome: str) -> Optional[Cidade]:
        return self.db.query(Cidade).filter(Cidade.nome == nome).first()

    def update(self, cidade: Cidade, dados: dict) -> Cidade:
        for campo, valor in dados.items():
            setattr(cidade, campo, valor)
        self.db.commit()
        self.db.refresh(cidade)
        return cidade

    def delete(self, cidade: Cidade) -> None:
        self.db.delete(cidade)
        self.db.commit()


# repository: hotel

class HotelRepository:
    """Acesso ao banco para Hotel com carregamento ansioso (joinedload)."""

    def __init__(self, db: Session):
        self.db = db

    def _query_com_relacoes(self):
        """Query base com joinedload para evitar N+1 em cidade e comodidades."""
        return self.db.query(Hotel).options(
            joinedload(Hotel.cidade),
            joinedload(Hotel.comodidades),
        )

    def create(
        self,
        nome: str,
        cidade_id: uuid.UUID,
        categoria_estrelas: int | None = None,
    ) -> Hotel:
        hotel = Hotel(
            nome=nome,
            cidade_id=cidade_id,
            categoria_estrelas=categoria_estrelas,
        )
        self.db.add(hotel)
        self.db.commit()
        self.db.refresh(hotel)
        return hotel

    def list(self) -> List[Hotel]:
        return self._query_com_relacoes().order_by(Hotel.nome).all()

    def list_by_cidade(self, cidade_id: uuid.UUID) -> List[Hotel]:
        return (
            self._query_com_relacoes()
            .filter(Hotel.cidade_id == cidade_id)
            .order_by(Hotel.nome)
            .all()
        )

    def get_by_id(self, hotel_id: uuid.UUID) -> Optional[Hotel]:
        return (
            self._query_com_relacoes()
            .filter(Hotel.id == hotel_id)
            .first()
        )

    def update(self, hotel: Hotel, dados: dict) -> Hotel:
        for campo, valor in dados.items():
            setattr(hotel, campo, valor)
        self.db.commit()
        self.db.refresh(hotel)
        return hotel

    def delete(self, hotel: Hotel) -> None:
        self.db.delete(hotel)
        self.db.commit()

    def adicionar_comodidade(self, hotel: Hotel, comodidade: Comodidade) -> Hotel:
        if comodidade not in hotel.comodidades:
            hotel.comodidades.append(comodidade)
            self.db.commit()
            self.db.refresh(hotel)
        return hotel

    def remover_comodidade(self, hotel: Hotel, comodidade: Comodidade) -> Hotel:
        if comodidade in hotel.comodidades:
            hotel.comodidades.remove(comodidade)
            self.db.commit()
            self.db.refresh(hotel)
        return hotel
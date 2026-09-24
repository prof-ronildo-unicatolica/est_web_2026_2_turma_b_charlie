import uuid
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.hotel import Cidade, Comodidade, Hotel, Quarto



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


 
class HotelRepository:
    def __init__(self, db: Session):
        self.db = db

    def _query_com_relacoes(self):
        """Carrega cidade, comodidades e quartos sem consultas N+1."""
        return self.db.query(Hotel).options(
            joinedload(Hotel.cidade),
            joinedload(Hotel.comodidades),
            joinedload(Hotel.quartos),
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
        return self.get_by_id(hotel.id)

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
        return self.get_by_id(hotel.id)

    def delete(self, hotel: Hotel) -> None:
        self.db.delete(hotel)
        self.db.commit()

    def adicionar_comodidade(self, hotel: Hotel, comodidade: Comodidade) -> Hotel:
        if comodidade not in hotel.comodidades:
            hotel.comodidades.append(comodidade)
            self.db.commit()
            self.db.refresh(hotel)
        return self.get_by_id(hotel.id)

    def remover_comodidade(self, hotel: Hotel, comodidade: Comodidade) -> Hotel:
        if comodidade in hotel.comodidades:
            hotel.comodidades.remove(comodidade)
            self.db.commit()
            self.db.refresh(hotel)
        return self.get_by_id(hotel.id)


 
class QuartoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
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
        quarto = Quarto(
            hotel_id=hotel_id,
            numero=numero,
            tipo=tipo,
            preco_diaria=preco_diaria,
            max_adultos=max_adultos,
            max_criancas=max_criancas,
            descricao=descricao,
            ativo=ativo,
        )
        self.db.add(quarto)
        self.db.commit()
        self.db.refresh(quarto)
        return quarto

    def get_by_id(self, quarto_id: uuid.UUID) -> Optional[Quarto]:
        return self.db.query(Quarto).filter(Quarto.id == quarto_id).first()

    def get_by_numero(self, hotel_id: uuid.UUID, numero: str) -> Optional[Quarto]:
        return (
            self.db.query(Quarto)
            .filter(Quarto.hotel_id == hotel_id, Quarto.numero == numero)
            .first()
        )

    def list_by_hotel(self, hotel_id: uuid.UUID) -> List[Quarto]:
        return (
            self.db.query(Quarto)
            .filter(Quarto.hotel_id == hotel_id)
            .order_by(Quarto.numero)
            .all()
        )

    def list_all(self) -> List[Quarto]:
        return self.db.query(Quarto).order_by(Quarto.numero).all()

    def update(self, quarto: Quarto, dados: dict) -> Quarto:
        for campo, valor in dados.items():
            setattr(quarto, campo, valor)
        self.db.commit()
        self.db.refresh(quarto)
        return quarto

    def delete(self, quarto: Quarto) -> None:
        self.db.delete(quarto)
        self.db.commit()
```
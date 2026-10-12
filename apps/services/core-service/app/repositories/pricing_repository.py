import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.hotel import ServicoAdicional, TarifaTemporada


class TarifaTemporadaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        hotel_id: uuid.UUID,
        nome: str,
        data_inicio,
        data_fim,
        multiplicador: float,
        ativo: bool = True,
    ) -> TarifaTemporada:
        tarifa = TarifaTemporada(
            hotel_id=hotel_id,
            nome=nome,
            data_inicio=data_inicio,
            data_fim=data_fim,
            multiplicador=multiplicador,
            ativo=ativo,
        )
        self.db.add(tarifa)
        self.db.commit()
        self.db.refresh(tarifa)
        return tarifa

    def list_by_hotel(self, hotel_id: uuid.UUID, apenas_ativas: bool = True) -> List[TarifaTemporada]:
        q = self.db.query(TarifaTemporada).filter(TarifaTemporada.hotel_id == hotel_id)
        if apenas_ativas:
            q = q.filter(TarifaTemporada.ativo.is_(True))
        return q.order_by(TarifaTemporada.data_inicio).all()

    def get_by_id(self, tarifa_id: uuid.UUID) -> Optional[TarifaTemporada]:
        return self.db.query(TarifaTemporada).filter(TarifaTemporada.id == tarifa_id).first()

    def update(self, tarifa: TarifaTemporada, **kwargs) -> TarifaTemporada:
        for key, value in kwargs.items():
            if value is not None and hasattr(tarifa, key):
                setattr(tarifa, key, value)
        self.db.commit()
        self.db.refresh(tarifa)
        return tarifa

    def delete(self, tarifa: TarifaTemporada) -> None:
        self.db.delete(tarifa)
        self.db.commit()


class ServicoAdicionalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        hotel_id: uuid.UUID,
        nome: str,
        preco: float,
        por_diaria: bool = True,
        descricao: Optional[str] = None,
        ativo: bool = True,
    ) -> ServicoAdicional:
        servico = ServicoAdicional(
            hotel_id=hotel_id,
            nome=nome,
            preco=preco,
            por_diaria=por_diaria,
            descricao=descricao,
            ativo=ativo,
        )
        self.db.add(servico)
        self.db.commit()
        self.db.refresh(servico)
        return servico

    def list_by_hotel(self, hotel_id: uuid.UUID, apenas_ativos: bool = True) -> List[ServicoAdicional]:
        q = self.db.query(ServicoAdicional).filter(ServicoAdicional.hotel_id == hotel_id)
        if apenas_ativos:
            q = q.filter(ServicoAdicional.ativo.is_(True))
        return q.order_by(ServicoAdicional.nome).all()

    def get_by_id(self, servico_id: uuid.UUID) -> Optional[ServicoAdicional]:
        return self.db.query(ServicoAdicional).filter(ServicoAdicional.id == servico_id).first()

    def list_by_ids(self, ids: List[uuid.UUID]) -> List[ServicoAdicional]:
        if not ids:
            return []
        return self.db.query(ServicoAdicional).filter(ServicoAdicional.id.in_(ids), ServicoAdicional.ativo.is_(True)).all()

    def update(self, servico: ServicoAdicional, **kwargs) -> ServicoAdicional:
        for key, value in kwargs.items():
            if value is not None and hasattr(servico, key):
                setattr(servico, key, value)
        self.db.commit()
        self.db.refresh(servico)
        return servico

    def delete(self, servico: ServicoAdicional) -> None:
        self.db.delete(servico)
        self.db.commit()
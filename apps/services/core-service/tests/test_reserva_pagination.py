import uuid
from datetime import date, datetime

from app.models.hotel import Cidade, Hotel, Quarto
from app.models.reserva import Reserva
from app.models.usuario import Usuario
from app.repositories.reserva_repository import ReservaRepository


def test_paginar_reservas_filtra_status_e_preserva_total(db_session):
    city = Cidade(id=uuid.uuid4(), nome="Fortaleza")
    hotel = Hotel(id=uuid.uuid4(), nome="Hotel Teste", cidade=city)
    room = Quarto(
        id=uuid.uuid4(),
        hotel=hotel,
        numero="101",
        tipo="Standard",
        preco_diaria=100.0,
        max_adultos=2,
        max_criancas=1,
        ativo=True,
    )
    user = Usuario(
        id=uuid.uuid4(),
        nome="Hóspede de Teste",
        email="hospede@example.com",
        senha_hash="hash",
        is_admin=False,
    )
    db_session.add_all([city, hotel, room, user])
    db_session.flush()

    reservas = [
        Reserva(
            id=uuid.uuid4(),
            usuario_id=user.id,
            quarto_id=room.id,
            checkin=date(2026, 12, 1),
            checkout=date(2026, 12, 2),
            adultos=1,
            criancas=0,
            bebes=0,
            valor_total=100.0,
            tipo_tarifa="reembolsavel",
            status=status,
            criado_em=datetime(2026, 11, 1, 0, minute),
            atualizado_em=datetime(2026, 11, 1, 0, minute),
        )
        for minute, status in enumerate(
            ("Confirmada", "Cancelada", "Confirmada"), start=1
        )
    ]
    db_session.add_all(reservas)
    db_session.commit()

    items, total = ReservaRepository(db_session).paginate_by_usuario_id(
        user.id, offset=1, limit=1, status="Confirmada"
    )

    assert total == 2
    assert len(items) == 1
    assert items[0].status == "Confirmada"
    assert items[0].criado_em == datetime(2026, 11, 1, 0, 1)

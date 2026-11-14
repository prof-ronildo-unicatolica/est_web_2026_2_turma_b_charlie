"""cancelamento_politicas

Revision ID: 009
Revises: 008
Create Date: 2026-11-05 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reservas",
        sa.Column("tipo_tarifa", sa.String(length=30), nullable=True, server_default="reembolsavel"),
    )
    op.add_column(
        "reservas",
        sa.Column("valor_multa", sa.Float(), nullable=True, server_default="0.0"),
    )
    op.add_column(
        "reservas",
        sa.Column("valor_reembolso", sa.Float(), nullable=True, server_default="0.0"),
    )
    op.add_column(
        "reservas",
        sa.Column("cancelado_em", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "reservas",
        sa.Column("motivo_cancelamento", sa.String(length=255), nullable=True),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE reservas SET tipo_tarifa = 'reembolsavel' WHERE tipo_tarifa IS NULL")
    )
    op.alter_column("reservas", "tipo_tarifa", nullable=False)


def downgrade() -> None:
    op.drop_column("reservas", "motivo_cancelamento")
    op.drop_column("reservas", "cancelado_em")
    op.drop_column("reservas", "valor_reembolso")
    op.drop_column("reservas", "valor_multa")
    op.drop_column("reservas", "tipo_tarifa")
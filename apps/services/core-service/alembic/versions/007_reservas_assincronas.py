"""reservas_assincronas

Revision ID: 007
Revises: 006
Create Date: 2026-10-19 19:00:00.000000
"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reservas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("quarto_id", sa.UUID(), nullable=False),
        sa.Column("checkin", sa.Date(), nullable=False),
        sa.Column("checkout", sa.Date(), nullable=False),
        sa.Column("adultos", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("criancas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bebes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valor_total", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pendente"),
        sa.Column("cotacao_snapshot", sa.JSON(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["quarto_id"], ["quartos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reservas_quarto_id", "reservas", ["quarto_id"])
    op.create_index("ix_reservas_status", "reservas", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reservas_status", table_name="reservas")
    op.drop_index("ix_reservas_quarto_id", table_name="reservas")
    op.drop_table("reservas")
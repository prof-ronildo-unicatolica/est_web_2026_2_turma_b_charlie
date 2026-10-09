"""cria tabela de quartos

Revision ID: 005
Revises: 004
Create Date: 2026-09-23 11:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quartos",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("preco_diaria", sa.Float(), nullable=False),
        sa.Column("max_adultos", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("max_criancas", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["hotel_id"],
            ["hoteis.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quartos_hotel_id"), "quartos", ["hotel_id"], unique=False)
    op.create_index(op.f("ix_quartos_ativo"), "quartos", ["ativo"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quartos_ativo"), table_name="quartos")
    op.drop_index(op.f("ix_quartos_hotel_id"), table_name="quartos")
    op.drop_table("quartos")
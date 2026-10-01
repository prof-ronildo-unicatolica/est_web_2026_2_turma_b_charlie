"""cria tabela de tarifas e servicos adicionais

Revision ID: 006
Revises: 005
Create Date: 2026-09-30 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tarifas_temporada",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=False),
        sa.Column("multiplicador", sa.Float(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hoteis.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "servicos_adicionais",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("preco", sa.Float(), nullable=False),
        sa.Column("por_diaria", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["hotel_id"], ["hoteis.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("servicos_adicionais")
    op.drop_table("tarifas_temporada")
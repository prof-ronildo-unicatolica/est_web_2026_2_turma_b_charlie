"""evolui cidades/hoteis e cria comodidades com relacao M:N

Revision ID: 004
Revises: 003
Create Date: 2026-09-21 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cidades",
        sa.Column(
            "limite_territorial",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )

    op.add_column(
        "hoteis",
        sa.Column("categoria_estrelas", sa.Integer(), nullable=True),
    )

    op.create_table(
        "comodidades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "hotel_comodidade",
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("comodidade_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["comodidade_id"], ["comodidades.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["hotel_id"], ["hoteis.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("hotel_id", "comodidade_id"),
    )


def downgrade() -> None:
    op.drop_table("hotel_comodidade")
    op.drop_table("comodidades")
    op.drop_column("hoteis", "categoria_estrelas")
    op.drop_column("cidades", "limite_territorial")
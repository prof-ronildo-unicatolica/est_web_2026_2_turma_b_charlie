"""cria as tabelas cidades e hoteis (relacao 1:N)

Revision ID: 002
Revises: 001
Create Date: 2026-08-24 10:00:00.000000

"""

from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Cria 'cidades' primeiro (tabela referenciada)
    op.create_table(
        "cidades",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )

    # 2. Cria 'hoteis' com a Foreign Key
    op.create_table(
        "hoteis",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("cidade_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["cidade_id"], ["cidades.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Cria índice explícito na FK (essencial para queries filtradas)
    op.create_index("ix_hoteis_cidade_id", "hoteis", ["cidade_id"])


def downgrade() -> None:
    # Ordem estritamente inversa
    op.drop_index("ix_hoteis_cidade_id", table_name="hoteis")
    op.drop_table("hoteis")
    op.drop_table("cidades")
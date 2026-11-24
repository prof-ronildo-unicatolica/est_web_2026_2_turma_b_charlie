"""sprint9_avaliacoes

Revision ID: 010_sprint9
Revises: 009
Create Date: 2026-11-23 23:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_sprint9"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "avaliacoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("reserva_id", sa.UUID(), nullable=False),
        sa.Column("hotel_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("nota", sa.Integer(), nullable=False),
        sa.Column("comentario", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "nota >= 1 AND nota <= 5",
            name="chk_avaliacao_nota_1_a_5",
        ),
        sa.ForeignKeyConstraint(
            ["reserva_id"],
            ["reservas.id"],
            name="fk_avaliacoes_reserva_id_reservas",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["hotel_id"],
            ["hoteis.id"],
            name="fk_avaliacoes_hotel_id_hoteis",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_avaliacoes_usuario_id_usuarios",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reserva_id",
            name="uq_avaliacoes_reserva_id",
        ),
    )
    op.create_index(
        "ix_avaliacoes_hotel_id",
        "avaliacoes",
        ["hotel_id"],
    )
    op.create_index(
        "ix_avaliacoes_usuario_id",
        "avaliacoes",
        ["usuario_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_avaliacoes_usuario_id", table_name="avaliacoes")
    op.drop_index("ix_avaliacoes_hotel_id", table_name="avaliacoes")
    op.drop_table("avaliacoes")

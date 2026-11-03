"""reserva_usuario

Revision ID: 008
Revises: 007
Create Date: 2026-10-20 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reservas", sa.Column("usuario_id", sa.UUID(), nullable=True))

    conn = op.get_bind()
    usuario_res = conn.execute(sa.text("SELECT id FROM usuarios LIMIT 1")).fetchone()
    if usuario_res:
        primeiro_usuario_id = usuario_res[0]
        conn.execute(
            sa.text(f"UPDATE reservas SET usuario_id = '{primeiro_usuario_id}' WHERE usuario_id IS NULL")
        )

    op.alter_column("reservas", "usuario_id", nullable=False)
    op.create_foreign_key(
        "fk_reservas_usuario_id_usuarios",
        "reservas",
        "usuarios",
        ["usuario_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_reservas_usuario_id", "reservas", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_reservas_usuario_id", table_name="reservas")
    op.drop_constraint("fk_reservas_usuario_id_usuarios", "reservas", type_="foreignkey")
    op.drop_column("reservas", "usuario_id")
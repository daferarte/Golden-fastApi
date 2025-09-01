"""rutina diaria vencidos

Revision ID: 752fb6684e29
Revises: 98a892b80664
Create Date: 2025-09-01 16:24:17.671735

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '752fb6684e29'
down_revision: Union[str, Sequence[str], None] = '98a892b80664'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Algunos motores requieren autocommit para CREATE PROCEDURE/EVENT
    with op.get_context().autocommit_block():
        # 1) Procedimiento: marca como VENCIDO cuando la fecha_fin ya pasó
        conn.exec_driver_sql("""
        CREATE PROCEDURE sp_marcar_membresias_vencidas()
        BEGIN
          UPDATE venta_membresia
          SET estado = 'VENCIDO'
          WHERE fecha_fin IS NOT NULL
            AND fecha_fin < CURDATE()    -- Expiradas antes de hoy
            AND estado <> 'VENCIDO';
        END
        """)

        # 2) Evento DIARIO: corre a la 01:10 AM hora del servidor
        conn.exec_driver_sql("""
        CREATE EVENT IF NOT EXISTS ev_marcar_vencidos_diario
        ON SCHEDULE EVERY 1 DAY
        STARTS (TIMESTAMP(CURDATE(), '03:10:00'))
        DO
          CALL sp_marcar_membresias_vencidas();
        """)


def downgrade() -> None:
    conn = op.get_bind()
    with op.get_context().autocommit_block():
        conn.exec_driver_sql("DROP EVENT IF EXISTS ev_marcar_vencidos_diario;")
        conn.exec_driver_sql("DROP PROCEDURE IF EXISTS sp_marcar_membresias_vencidas;")

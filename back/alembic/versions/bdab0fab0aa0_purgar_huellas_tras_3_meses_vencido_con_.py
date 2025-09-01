"""purgar huellas tras 3 meses vencido (con log)

Revision ID: bdab0fab0aa0
Revises: 782d348160f0
Create Date: 2025-08-31 21:19:01.094293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdab0fab0aa0'
down_revision: Union[str, Sequence[str], None] = '782d348160f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    with op.get_context().autocommit_block():
        # 1) Log para el informe (sin guardar plantilla biométrica)
        conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS huella_purgada_log (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            cliente_id BIGINT NOT NULL,
            venta_membresia_id BIGINT NULL,
            fecha_purgado DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_fin_ultima_membresia DATE NOT NULL,
            id_huella_prev VARCHAR(255) NULL,
            tenia_template TINYINT(1) NOT NULL,
            nombre VARCHAR(200) NULL,
            apellido VARCHAR(200) NULL,
            documento VARCHAR(100) NULL,
            correo VARCHAR(255) NULL,
            motivo ENUM('VENCIDO_3_MESES') NOT NULL DEFAULT 'VENCIDO_3_MESES',
            KEY idx_hp_log_cliente (cliente_id),
            KEY idx_hp_log_fecha (fecha_purgado),
            KEY idx_hp_log_ultfin (fecha_fin_ultima_membresia)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 2) SP: purga biometría si la ÚLTIMA membresía terminó hace ≥ 3 meses
        conn.exec_driver_sql("""
        CREATE PROCEDURE sp_purgar_huellas_por_vencimiento_3m()
        BEGIN
          INSERT INTO huella_purgada_log (
            cliente_id, venta_membresia_id, fecha_fin_ultima_membresia,
            id_huella_prev, tenia_template, nombre, apellido, documento, correo, motivo
          )
          SELECT
            c.id,
            vm_last.id,
            vm_last.fecha_fin,
            c.id_huella,
            (c.huella_template IS NOT NULL AND LENGTH(c.huella_template) > 0),
            c.nombre, c.apellido, c.documento, c.correo,
            'VENCIDO_3_MESES'
          FROM cliente c
          JOIN (
              SELECT vm1.id, vm1.id_cliente, vm1.fecha_fin
              FROM venta_membresia vm1
              JOIN (
                  SELECT id_cliente, MAX(fecha_fin) AS max_fecha
                  FROM venta_membresia
                  GROUP BY id_cliente
              ) m ON m.id_cliente = vm1.id_cliente AND m.max_fecha = vm1.fecha_fin
          ) vm_last ON vm_last.id_cliente = c.id
          WHERE (c.id_huella IS NOT NULL OR c.huella_template IS NOT NULL)
            AND vm_last.fecha_fin IS NOT NULL
            AND vm_last.fecha_fin < (CURDATE() - INTERVAL 3 MONTH)
            AND EXISTS (
              SELECT 1 FROM venta_membresia vm2
              WHERE vm2.id = vm_last.id
                AND (vm2.estado = 'VENCIDO' OR vm2.fecha_fin < CURDATE())
            );

          UPDATE cliente c
          JOIN (
              SELECT vm1.id_cliente, vm1.fecha_fin
              FROM venta_membresia vm1
              JOIN (
                  SELECT id_cliente, MAX(fecha_fin) AS max_fecha
                  FROM venta_membresia
                  GROUP BY id_cliente
              ) m ON m.id_cliente = vm1.id_cliente AND m.max_fecha = vm1.fecha_fin
          ) vm_last ON vm_last.id_cliente = c.id
          SET c.id_huella = NULL,
              c.huella_template = NULL
          WHERE (c.id_huella IS NOT NULL OR c.huella_template IS NOT NULL)
            AND vm_last.fecha_fin IS NOT NULL
            AND vm_last.fecha_fin < (CURDATE() - INTERVAL 3 MONTH);
        END
        """)

        # 3) Evento diario a las 09:20 AM (no choca con el de vencidos a las 01:10)
        conn.exec_driver_sql("""
        CREATE EVENT IF NOT EXISTS ev_purgar_huellas_vencido_3m
        ON SCHEDULE EVERY 1 DAY
        STARTS (TIMESTAMP(CURDATE(), '09:20:00'))
        DO
          CALL sp_purgar_huellas_por_vencimiento_3m();
        """)

        # 4) Vista de informe
        conn.exec_driver_sql("""
        CREATE OR REPLACE VIEW vw_informe_huellas_purgadas AS
        SELECT
          id, fecha_purgado, cliente_id, venta_membresia_id,
          fecha_fin_ultima_membresia, id_huella_prev, tenia_template,
          nombre, apellido, documento, correo, motivo
        FROM huella_purgada_log;
        """)

        # 5) (Opcional) SP de reporte por rango
        conn.exec_driver_sql("""
        CREATE PROCEDURE sp_reporte_huellas_purgadas(IN p_desde DATETIME, IN p_hasta DATETIME)
        BEGIN
          SELECT *
          FROM vw_informe_huellas_purgadas
          WHERE fecha_purgado >= p_desde AND fecha_purgado < p_hasta
          ORDER BY fecha_purgado DESC;
        END
        """)


def downgrade() -> None:
    conn = op.get_bind()
    with op.get_context().autocommit_block():
        conn.exec_driver_sql("DROP EVENT IF EXISTS ev_purgar_huellas_vencido_3m;")
        conn.exec_driver_sql("DROP PROCEDURE IF EXISTS sp_reporte_huellas_purgadas;")
        conn.exec_driver_sql("DROP VIEW IF EXISTS vw_informe_huellas_purgadas;")
        conn.exec_driver_sql("DROP PROCEDURE IF EXISTS sp_purgar_huellas_por_vencimiento_3m;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS huella_purgada_log;")

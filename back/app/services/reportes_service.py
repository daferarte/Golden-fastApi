from datetime import date, timedelta, datetime, time
from sqlalchemy import func, select, desc, case, and_, extract
from sqlalchemy.orm import Session
from app.models.venta_membresia import VentaMembresia
from typing import List, Dict
from app.models.asistencia import Asistencia


class ReportesService:
    """
    Reportes agregados sobre el estado de membresías por cliente.
    Toma la última venta por cliente (fecha_inicio más reciente).
    """

    def resumen_membresias(self, db: Session, dias_alerta: int = 5) -> dict:
        """
        Retorna:
        {
          "total_clientes": int,
          "activos": int,
          "proximos_vencer": int,
          "vencidos": int
        }
        """
        # 1) Subconsulta: última venta por cliente usando ventana
        rn = func.row_number().over(
            partition_by=VentaMembresia.id_cliente,
            order_by=(desc(VentaMembresia.fecha_inicio), desc(VentaMembresia.id))
        ).label("rn")

        latest_sq = (
            select(
                VentaMembresia.id_cliente,
                VentaMembresia.fecha_inicio,
                VentaMembresia.fecha_fin,
                # VentaMembresia.estado,  # descomenta si quieres condicionar por estado
                rn,
            )
        ).subquery("latest")

        # 2) Fechas de referencia
        hoy: date = date.today()
        corte: date = hoy + timedelta(days=dias_alerta)

        # 3) Clasificaciones
        # Activo: hoy ∈ [inicio, fin]
        activo_case = case(
            ((latest_sq.c.fecha_inicio <= hoy) & (latest_sq.c.fecha_fin >= hoy), 1),
            else_=0
        )
        # Próximo a vencer: activo y fin < hoy + dias_alerta
        prox_case = case(
            (
                (latest_sq.c.fecha_inicio <= hoy)
                & (latest_sq.c.fecha_fin >= hoy)
                & (latest_sq.c.fecha_fin < corte),
                1
            ),
            else_=0
        )
        # Vencido: fin < hoy
        vencido_case = case((latest_sq.c.fecha_fin < hoy, 1), else_=0)

        stmt = (
            select(
                func.count().label("total_clientes"),
                func.sum(activo_case).label("activos"),
                func.sum(prox_case).label("proximos_vencer"),
                func.sum(vencido_case).label("vencidos"),
            )
            .where(latest_sq.c.rn == 1)
        )

        row = db.execute(stmt).one()
        return {
            "total_clientes": int(row.total_clientes or 0),
            "activos": int(row.activos or 0),
            "proximos_vencer": int(row.proximos_vencer or 0),
            "vencidos": int(row.vencidos or 0),
        }

    # ---------- RESUMEN: hoy / mes / año ----------
    def resumen_asistencias(self, db: Session) -> dict:
        hoy = date.today()

        # Límites por rango
        start_dia = datetime.combine(hoy, time.min)
        end_dia   = start_dia + timedelta(days=1)

        start_mes = start_dia.replace(day=1)
        # siguiente mes:
        if start_mes.month == 12:
            next_month = start_mes.replace(year=start_mes.year + 1, month=1, day=1)
        else:
            next_month = start_mes.replace(month=start_mes.month + 1, day=1)

        start_anio = start_dia.replace(month=1, day=1)
        next_year  = start_anio.replace(year=start_anio.year + 1, month=1, day=1)

        # Filters: Exclude Staff (id_venta is NULL)
        common_filters = [Asistencia.id_venta != None]

        q_dia = select(func.count()).where(
            and_(
                Asistencia.fecha_hora_entrada >= start_dia,
                Asistencia.fecha_hora_entrada <  end_dia,
                *common_filters
            )
        )
        q_mes = select(func.count()).where(
            and_(
                Asistencia.fecha_hora_entrada >= start_mes,
                Asistencia.fecha_hora_entrada <  next_month,
                *common_filters
            )
        )
        q_anio = select(func.count()).where(
            and_(
                Asistencia.fecha_hora_entrada >= start_anio,
                Asistencia.fecha_hora_entrada <  next_year,
                *common_filters
            )
        )

        dia  = db.execute(q_dia).scalar_one()
        mes  = db.execute(q_mes).scalar_one()
        anio = db.execute(q_anio).scalar_one()

        return {
            "diarias_hoy": int(dia),
            "mensuales_actual": int(mes),
            "anuales_actual": int(anio),
        }

    # ---------- SERIES: diarias en los últimos N días ----------
    def serie_asistencias_diarias(self, db: Session, dias: int = 30) -> List[Dict]:
        """
        Retorna [{"fecha": "YYYY-MM-DD", "total": N}, ...] para los últimos `dias`.
        Only clients (id_venta != None).
        """
        fin   = datetime.combine(date.today(), time.min) + timedelta(days=1)
        inicio = fin - timedelta(days=dias)

        stmt = (
            select(func.date(Asistencia.fecha_hora_entrada).label("dia"),
                   func.count().label("total"))
            .where(and_(
                Asistencia.fecha_hora_entrada >= inicio,
                Asistencia.fecha_hora_entrada <  fin,
                Asistencia.id_venta != None
            ))
            .group_by("dia")
            .order_by("dia")
        )
        rows = db.execute(stmt).all()
        return [{"fecha": r.dia.isoformat(), "total": int(r.total)} for r in rows]

    # ---------- SERIES: mensuales en los últimos N meses ----------
    def serie_asistencias_mensuales(self, db: Session, meses: int = 12) -> List[Dict]:
        """
        Retorna [{"anio": 2025, "mes": 9, "total": N}, ...]
        Only clients (id_venta != None).
        """
        hoy = date.today()
        start_mes = date(hoy.year, hoy.month, 1)
        y, m = start_mes.year, start_mes.month
        m -= (meses - 1)
        while m <= 0:
            m += 12
            y -= 1
        inicio = datetime.combine(date(y, m, 1), time.min)

        if hoy.month == 12:
            fin = datetime.combine(date(hoy.year + 1, 1, 1), time.min)
        else:
            fin = datetime.combine(date(hoy.year, hoy.month + 1, 1), time.min)

        stmt = (
            select(
                extract("year", Asistencia.fecha_hora_entrada).label("anio"),
                extract("month", Asistencia.fecha_hora_entrada).label("mes"),
                func.count().label("total"),
            )
            .where(and_(
                Asistencia.fecha_hora_entrada >= inicio,
                Asistencia.fecha_hora_entrada <  fin,
                Asistencia.id_venta != None
            ))
            .group_by("anio", "mes")
            .order_by("anio", "mes")
        )
        rows = db.execute(stmt).all()
        return [{"anio": int(r.anio), "mes": int(r.mes), "total": int(r.total)} for r in rows]

    # ---------- SERIES: anuales en los últimos N años ----------
    def serie_asistencias_anuales(self, db: Session, anios: int = 5) -> List[Dict]:
        """
        Retorna [{"anio": 2021, "total": N}, ...]
        Only clients (id_venta != None).
        """
        anio_actual = date.today().year
        inicio = datetime.combine(date(anio_actual - (anios - 1), 1, 1), time.min)
        fin    = datetime.combine(date(anio_actual + 1, 1, 1), time.min)

        stmt = (
            select(
                extract("year", Asistencia.fecha_hora_entrada).label("anio"),
                func.count().label("total"),
            )
            .where(and_(
                Asistencia.fecha_hora_entrada >= inicio,
                Asistencia.fecha_hora_entrada <  fin,
                Asistencia.id_venta != None
            ))
            .group_by("anio")
            .order_by("anio")
        )
        rows = db.execute(stmt).all()
        return [{"anio": int(r.anio), "total": int(r.total)} for r in rows]
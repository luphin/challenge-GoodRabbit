from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Shift
from app.schemas.report import (
    DailyMetrics,
    EmployeeReport,
    EmployeeReportMetrics,
    WeeklyMetrics,
)
from app.services import employee_service, shift_service, validators


def build_employee_report(
    db: Session,
    *,
    employee_id: int,
    report_date: date,
    date_from: date | None,
    date_to: date | None,
    limit: int,
    offset: int,
) -> EmployeeReport:
    employee = employee_service.get_employee(db, employee_id)
    assignment = employee.rule_assignment
    rule = assignment.shift_rule if assignment is not None else None

    metrics = None
    if rule is not None:
        day_hours = shift_service.assigned_hours(
            db, employee_id, report_date, report_date
        )
        week_start, week_end = validators.week_bounds(report_date)
        week_hours = shift_service.assigned_hours(db, employee_id, week_start, week_end)
        metrics = EmployeeReportMetrics(
            daily=DailyMetrics(
                shift_date=report_date,
                assigned_hours=_fmt(day_hours),
                max_hours=_fmt(rule.max_hours_day),
                remaining_hours=_fmt(rule.max_hours_day - day_hours),
                usage_percent=_percent(day_hours, rule.max_hours_day),
            ),
            weekly=WeeklyMetrics(
                week_start=week_start,
                week_end=week_end,
                assigned_hours=_fmt(week_hours),
                max_hours=_fmt(rule.max_hours_week),
                remaining_hours=_fmt(rule.max_hours_week - week_hours),
                usage_percent=_percent(week_hours, rule.max_hours_week),
            ),
        )

    stmt = select(Shift).where(Shift.employee_id == employee_id)
    count_stmt = (
        select(func.count()).select_from(Shift).where(Shift.employee_id == employee_id)
    )
    if date_from is not None:
        stmt = stmt.where(Shift.shift_date >= date_from)
        count_stmt = count_stmt.where(Shift.shift_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Shift.shift_date <= date_to)
        count_stmt = count_stmt.where(Shift.shift_date <= date_to)

    stmt = stmt.order_by(Shift.shift_date, Shift.start_time).offset(offset).limit(limit)
    shifts = list(db.scalars(stmt).all())
    shifts_total = db.scalar(count_stmt) or 0

    return EmployeeReport(
        employee=employee,
        shift_rule=rule,
        metrics=metrics,
        shifts=shifts,
        shifts_total=shifts_total,
    )


def _fmt(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01")))


def _percent(assigned: Decimal, maximum: Decimal) -> float:
    if maximum == 0:
        return 0.0
    return float((assigned / maximum * 100).quantize(Decimal("0.1")))

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BulkValidationError,
    ConflictError,
    NotFoundError,
    RuleViolationError,
)
from app.models import Shift, ShiftRule
from app.schemas.shift import ShiftBulkError, ShiftCreate, ShiftUpdate
from app.services import employee_service, validators


def list_shifts(
    db: Session,
    *,
    employee_id: int | None,
    date_from: date | None,
    date_to: date | None,
    limit: int,
    offset: int,
) -> tuple[list[Shift], int]:
    stmt = select(Shift)
    count_stmt = select(func.count()).select_from(Shift)

    if employee_id is not None:
        stmt = stmt.where(Shift.employee_id == employee_id)
        count_stmt = count_stmt.where(Shift.employee_id == employee_id)
    if date_from is not None:
        stmt = stmt.where(Shift.shift_date >= date_from)
        count_stmt = count_stmt.where(Shift.shift_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Shift.shift_date <= date_to)
        count_stmt = count_stmt.where(Shift.shift_date <= date_to)

    stmt = stmt.order_by(Shift.shift_date, Shift.start_time).offset(offset).limit(limit)
    shifts = list(db.scalars(stmt).all())
    total = db.scalar(count_stmt) or 0
    return shifts, total


def get_shift(db: Session, shift_id: int) -> Shift:
    shift = db.get(Shift, shift_id)
    if shift is None:
        raise NotFoundError(f"El turno {shift_id} no existe")
    return shift


def create_shift(db: Session, data: ShiftCreate) -> Shift:
    _validate_shift(
        db,
        employee_id=data.employee_id,
        shift_date=data.shift_date,
        start_time=data.start_time,
        end_time=data.end_time,
        exclude_shift_id=None,
    )
    shift = Shift(**data.model_dump())
    db.add(shift)
    db.flush()
    return shift


def update_shift(db: Session, shift_id: int, data: ShiftUpdate) -> Shift:
    shift = get_shift(db, shift_id)
    changes = data.model_dump(exclude_unset=True)

    employee_id = changes.get("employee_id", shift.employee_id)
    shift_date = changes.get("shift_date", shift.shift_date)
    start_time = changes.get("start_time", shift.start_time)
    end_time = changes.get("end_time", shift.end_time)

    _validate_shift(
        db,
        employee_id=employee_id,
        shift_date=shift_date,
        start_time=start_time,
        end_time=end_time,
        exclude_shift_id=shift.shift_id,
    )

    for key, value in changes.items():
        setattr(shift, key, value)
    db.flush()
    return shift


def delete_shift(db: Session, shift_id: int) -> None:
    shift = get_shift(db, shift_id)
    db.delete(shift)
    db.flush()


def bulk_create_shifts(db: Session, items: list[ShiftCreate]) -> list[Shift]:
    errors: list[ShiftBulkError] = []
    created: list[Shift] = []

    for index, item in enumerate(items):
        try:
            _validate_shift(
                db,
                employee_id=item.employee_id,
                shift_date=item.shift_date,
                start_time=item.start_time,
                end_time=item.end_time,
                exclude_shift_id=None,
            )
        except (RuleViolationError, NotFoundError, ConflictError) as exc:
            errors.append(
                ShiftBulkError(
                    index=index,
                    employee_id=item.employee_id,
                    shift_date=item.shift_date,
                    causa=str(exc),
                )
            )
            continue
        shift = Shift(**item.model_dump())
        db.add(shift)
        db.flush()
        created.append(shift)

    if errors:
        raise BulkValidationError(errors)
    return created


def assigned_hours(
    db: Session,
    employee_id: int,
    date_from: date,
    date_to: date,
    *,
    exclude_shift_id: int | None = None,
) -> Decimal:
    stmt = (
        select(Shift)
        .where(Shift.employee_id == employee_id)
        .where(Shift.shift_date >= date_from)
        .where(Shift.shift_date <= date_to)
    )
    if exclude_shift_id is not None:
        stmt = stmt.where(Shift.shift_id != exclude_shift_id)
    shifts = db.scalars(stmt).all()
    return sum(
        (validators.shift_duration_hours(s.start_time, s.end_time) for s in shifts),
        Decimal(0),
    )


def _validate_shift(
    db: Session,
    *,
    employee_id: int,
    shift_date: date,
    start_time: time,
    end_time: time,
    exclude_shift_id: int | None,
) -> None:
    rule = _get_employee_rule(db, employee_id)
    validators.validate_times(start_time, end_time)
    shift_hours = validators.shift_duration_hours(start_time, end_time)
    new_start, new_end = validators.shift_bounds(shift_date, start_time, end_time)

    overlapping = _find_overlap(
        db,
        employee_id=employee_id,
        shift_date=shift_date,
        start_time=start_time,
        end_time=end_time,
        exclude_shift_id=exclude_shift_id,
    )
    validators.validate_no_overlap(
        employee_id=employee_id,
        new_start=new_start,
        new_end=new_end,
        overlapping=overlapping,
    )

    existing_day = assigned_hours(
        db, employee_id, shift_date, shift_date, exclude_shift_id=exclude_shift_id
    )
    validators.validate_daily_limit(
        employee_id=employee_id,
        shift_date=shift_date,
        existing_hours=existing_day,
        shift_hours=shift_hours,
        max_hours_day=rule.max_hours_day,
    )

    week_start, week_end = validators.week_bounds(shift_date)
    existing_week = assigned_hours(
        db, employee_id, week_start, week_end, exclude_shift_id=exclude_shift_id
    )
    validators.validate_weekly_limit(
        employee_id=employee_id,
        week_start=week_start,
        week_end=week_end,
        existing_hours=existing_week,
        shift_hours=shift_hours,
        max_hours_week=rule.max_hours_week,
    )


def _get_employee_rule(db: Session, employee_id: int) -> ShiftRule:
    employee = employee_service.get_employee(db, employee_id)
    if employee.status == "inactive":
        raise ConflictError(
            f"El empleado {employee_id} está inactivo y no puede recibir turnos"
        )
    if employee.rule_assignment is None:
        raise RuleViolationError(
            f"El empleado {employee_id} no tiene una regla laboral asignada; "
            f"asigne una antes de programar turnos"
        )
    return employee.rule_assignment.shift_rule


def _find_overlap(
    db: Session,
    *,
    employee_id: int,
    shift_date: date,
    start_time: time,
    end_time: time,
    exclude_shift_id: int | None,
) -> tuple[datetime, datetime] | None:
    stmt = (
        select(Shift)
        .where(Shift.employee_id == employee_id)
        .where(Shift.shift_date >= shift_date - timedelta(days=1))
        .where(Shift.shift_date <= shift_date + timedelta(days=1))
    )
    if exclude_shift_id is not None:
        stmt = stmt.where(Shift.shift_id != exclude_shift_id)

    new_start, new_end = validators.shift_bounds(shift_date, start_time, end_time)
    for other in db.scalars(stmt).all():
        other_start, other_end = validators.shift_bounds(
            other.shift_date, other.start_time, other.end_time
        )
        if new_start < other_end and other_start < new_end:
            return other_start, other_end
    return None

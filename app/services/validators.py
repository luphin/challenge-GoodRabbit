from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.core.exceptions import RuleViolationError

_SECONDS_PER_DAY = 86400


def _time_seconds(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def shift_duration_seconds(start_time: time, end_time: time) -> int:
    start_s = _time_seconds(start_time)
    end_s = _time_seconds(end_time)
    if end_s < start_s:
        return _SECONDS_PER_DAY - start_s + end_s
    return end_s - start_s


def shift_duration_hours(start_time: time, end_time: time) -> Decimal:
    return Decimal(shift_duration_seconds(start_time, end_time)) / Decimal(3600)


def is_overnight(start_time: time, end_time: time) -> bool:
    return _time_seconds(end_time) < _time_seconds(start_time)


def shift_bounds(
    shift_date: date, start_time: time, end_time: time
) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(shift_date, start_time)
    end_dt = start_dt + timedelta(seconds=shift_duration_seconds(start_time, end_time))
    return start_dt, end_dt


def week_bounds(shift_date: date) -> tuple[date, date]:
    monday = shift_date - timedelta(days=shift_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def validate_times(start_time: time, end_time: time) -> None:
    if end_time == start_time:
        raise RuleViolationError(
            "La duración del turno debe ser mayor a cero; una hora de fin igual a "
            "la de inicio no es válida. Un fin menor al inicio se interpreta como "
            "turno nocturno que cruza la medianoche"
        )


def validate_daily_limit(
    *,
    employee_id: int,
    shift_date: date,
    existing_hours: Decimal,
    shift_hours: Decimal,
    max_hours_day: Decimal,
) -> None:
    total = existing_hours + shift_hours
    if total > max_hours_day:
        excedente = total - max_hours_day
        raise RuleViolationError(
            f"El empleado {employee_id} excede el límite diario de "
            f"{_format_hours(max_hours_day)}h del {shift_date}: ya tiene "
            f"{_format_hours(existing_hours)}h asignadas y el turno aporta "
            f"{_format_hours(shift_hours)}h (excedente: {_format_hours(excedente)}h)"
        )


def validate_weekly_limit(
    *,
    employee_id: int,
    week_start: date,
    week_end: date,
    existing_hours: Decimal,
    shift_hours: Decimal,
    max_hours_week: Decimal,
) -> None:
    total = existing_hours + shift_hours
    if total > max_hours_week:
        excedente = total - max_hours_week
        raise RuleViolationError(
            f"El empleado {employee_id} excede el límite semanal de "
            f"{_format_hours(max_hours_week)}h de la semana del {week_start} al "
            f"{week_end}: ya tiene {_format_hours(existing_hours)}h asignadas y el "
            f"turno aporta {_format_hours(shift_hours)}h "
            f"(excedente: {_format_hours(excedente)}h)"
        )


def validate_no_overlap(
    *,
    employee_id: int,
    new_start: datetime,
    new_end: datetime,
    overlapping: tuple[datetime, datetime] | None,
) -> None:
    if overlapping is not None and new_start < overlapping[1] and overlapping[0] < new_end:
        raise RuleViolationError(
            f"El empleado {employee_id} ya tiene un turno de "
            f"{_format_datetime(overlapping[0])} a {_format_datetime(overlapping[1])} "
            f"que se traslapa con el nuevo turno "
            f"({_format_datetime(new_start)} a {_format_datetime(new_end)})"
        )


def _format_hours(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral_value():
        return str(normalized.quantize(Decimal("1")))
    return str(normalized)


def _format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M")

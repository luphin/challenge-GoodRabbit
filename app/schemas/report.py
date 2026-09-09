from datetime import date

from pydantic import BaseModel

from app.schemas.employee import EmployeeRead
from app.schemas.shift import ShiftRead
from app.schemas.shift_rule import ShiftRuleRead


class UsageMetrics(BaseModel):
    assigned_hours: str
    max_hours: str
    remaining_hours: str
    usage_percent: float


class DailyMetrics(UsageMetrics):
    shift_date: date


class WeeklyMetrics(UsageMetrics):
    week_start: date
    week_end: date


class EmployeeReportMetrics(BaseModel):
    daily: DailyMetrics
    weekly: WeeklyMetrics


class EmployeeReport(BaseModel):
    employee: EmployeeRead
    shift_rule: ShiftRuleRead | None
    metrics: EmployeeReportMetrics | None
    shifts: list[ShiftRead]
    shifts_total: int

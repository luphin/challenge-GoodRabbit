from datetime import date, time

from pydantic import BaseModel, ConfigDict


class ShiftCreate(BaseModel):
    employee_id: int
    shift_date: date
    start_time: time
    end_time: time


class ShiftUpdate(BaseModel):
    employee_id: int | None = None
    shift_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None


class ShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    shift_id: int
    employee_id: int
    shift_date: date
    start_time: time
    end_time: time


class ShiftBulkError(BaseModel):
    index: int
    employee_id: int | None = None
    shift_date: date | None = None
    causa: str


class ShiftBulkCreated(BaseModel):
    total: int
    items: list[ShiftRead]

from datetime import date, time

from sqlalchemy import Date, ForeignKey, Index, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.employee import Employee


class Shift(Base):
    __tablename__ = "shifts"
    __table_args__ = (
        Index("ix_shifts_employee_date", "employee_id", "shift_date"),
    )

    shift_id: Mapped[int] = mapped_column(primary_key=True)
    shift_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))

    employee: Mapped["Employee"] = relationship(back_populates="shifts")

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.shift import Shift
    from app.models.shift_rule_employee import ShiftRuleEmployee


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')", name="ck_employees_status_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    last_name: Mapped[str]
    phone_number: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(default="active", server_default="active")

    shifts: Mapped[list["Shift"]] = relationship(back_populates="employee")
    rule_assignment: Mapped["ShiftRuleEmployee | None"] = relationship(
        back_populates="employee", uselist=False
    )

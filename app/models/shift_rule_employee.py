from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.shift_rule import ShiftRule


class ShiftRuleEmployee(Base):
    __tablename__ = "shift_rules_employees"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_shift_rules_employees_employee_id"),
    )

    shift_rule_r_employee_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))
    shift_rule_id: Mapped[int] = mapped_column(ForeignKey("shift_rules.shift_rule_id"))

    employee: Mapped["Employee"] = relationship(back_populates="rule_assignment")
    shift_rule: Mapped["ShiftRule"] = relationship(back_populates="rule_assignments")

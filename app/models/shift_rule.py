from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.shift_rule_employee import ShiftRuleEmployee


class ShiftRule(Base):
    __tablename__ = "shift_rules"
    __table_args__ = (
        CheckConstraint(
            "max_hours_day > 0", name="ck_shift_rules_max_hours_day_positive"
        ),
        CheckConstraint(
            "max_hours_week > 0", name="ck_shift_rules_max_hours_week_positive"
        ),
    )

    shift_rule_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    max_hours_day: Mapped[Decimal] = mapped_column(Numeric(4, 2))
    max_hours_week: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    rule_assignments: Mapped[list["ShiftRuleEmployee"]] = relationship(
        back_populates="shift_rule"
    )

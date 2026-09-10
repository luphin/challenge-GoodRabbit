from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, RuleViolationError
from app.models import ShiftRule
from app.schemas.shift_rule import ShiftRuleCreate, ShiftRuleUpdate


def list_shift_rules(
    db: Session, *, name: str | None, limit: int, offset: int
) -> tuple[list[ShiftRule], int]:
    stmt = select(ShiftRule)
    count_stmt = select(func.count()).select_from(ShiftRule)

    if name is not None:
        stmt = stmt.where(ShiftRule.name.ilike(f"%{name}%"))
        count_stmt = count_stmt.where(ShiftRule.name.ilike(f"%{name}%"))

    stmt = stmt.order_by(ShiftRule.shift_rule_id).offset(offset).limit(limit)
    rules = list(db.scalars(stmt).all())
    total = db.scalar(count_stmt) or 0
    return rules, total


def get_shift_rule(db: Session, shift_rule_id: int) -> ShiftRule:
    rule = db.get(ShiftRule, shift_rule_id)
    if rule is None:
        raise NotFoundError(f"La regla laboral {shift_rule_id} no existe")
    return rule


def create_shift_rule(db: Session, data: ShiftRuleCreate) -> ShiftRule:
    #TODO: faltaria validar la existencia de otra con el mismo:
    # "name", "max_hours_day", "max_hours_week"
    rule = ShiftRule(**data.model_dump())
    db.add(rule)
    db.flush()
    return rule


def update_shift_rule(
    db: Session, shift_rule_id: int, data: ShiftRuleUpdate
) -> ShiftRule:
    rule = get_shift_rule(db, shift_rule_id)
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(rule, key, value)
    if rule.max_hours_week < rule.max_hours_day:
        raise RuleViolationError(
            "max_hours_week no puede ser menor que max_hours_day"
        )
    db.flush()
    return rule


def delete_shift_rule(db: Session, shift_rule_id: int) -> None:
    rule = get_shift_rule(db, shift_rule_id)
    if rule.rule_assignments:
        raise ConflictError(
            f"La regla '{rule.name}' está asignada a empleados y no se puede eliminar"
        )
    db.delete(rule)
    db.flush()

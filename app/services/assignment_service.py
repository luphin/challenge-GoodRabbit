from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models import Employee, ShiftRule, ShiftRuleEmployee
from app.schemas.shift_rule_employee import ShiftRuleEmployeeCreate, ShiftRuleEmployeeUpdate


def list_assignments(
    db: Session, *, employee_id: int | None, limit: int, offset: int
) -> tuple[list[ShiftRuleEmployee], int]:
    stmt = select(ShiftRuleEmployee)
    count_stmt = select(func.count()).select_from(ShiftRuleEmployee)

    if employee_id is not None:
        stmt = stmt.where(ShiftRuleEmployee.employee_id == employee_id)
        count_stmt = count_stmt.where(ShiftRuleEmployee.employee_id == employee_id)

    stmt = stmt.order_by(ShiftRuleEmployee.shift_rule_r_employee_id).offset(offset).limit(limit)
    assignments = list(db.scalars(stmt).all())
    total = db.scalar(count_stmt) or 0
    return assignments, total


def get_assignment(db: Session, shift_rule_r_employee_id: int) -> ShiftRuleEmployee:
    assignment = db.get(ShiftRuleEmployee, shift_rule_r_employee_id)
    if assignment is None:
        raise NotFoundError(
            f"La asignación {shift_rule_r_employee_id} no existe"
        )
    return assignment


def create_assignment(
    db: Session, data: ShiftRuleEmployeeCreate
) -> ShiftRuleEmployee:
    if db.get(Employee, data.employee_id) is None:
        raise BusinessRuleError(f"El empleado {data.employee_id} no existe")
    if db.get(ShiftRule, data.shift_rule_id) is None:
        raise BusinessRuleError(f"La regla laboral {data.shift_rule_id} no existe")

    existing = db.scalar(
        select(ShiftRuleEmployee).where(
            ShiftRuleEmployee.employee_id == data.employee_id
        )
    )
    if existing is not None:
        rule_name = existing.shift_rule.name
        raise ConflictError(
            f"El empleado {data.employee_id} ya tiene la regla '{rule_name}' asignada"
        )

    assignment = ShiftRuleEmployee(
        employee_id=data.employee_id,
        shift_rule_id=data.shift_rule_id,
    )
    db.add(assignment)
    db.flush()
    return assignment


def update_assignment(
    db: Session, shift_rule_r_employee_id: int, data: ShiftRuleEmployeeUpdate
) -> ShiftRuleEmployee:
    assignment = get_assignment(db, shift_rule_r_employee_id)
    if db.get(ShiftRule, data.shift_rule_id) is None:
        raise BusinessRuleError(f"La regla laboral {data.shift_rule_id} no existe")
    assignment.shift_rule_id = data.shift_rule_id
    db.flush()
    return assignment


def delete_assignment(db: Session, shift_rule_r_employee_id: int) -> None:
    assignment = get_assignment(db, shift_rule_r_employee_id)
    db.delete(assignment)
    db.flush()

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def list_employees(
    db: Session,
    *,
    email: str | None,
    name: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Employee], int]:
    stmt = select(Employee)
    count_stmt = select(func.count()).select_from(Employee)

    if email is not None:
        stmt = stmt.where(Employee.email == email)
        count_stmt = count_stmt.where(Employee.email == email)
    if name is not None:
        stmt = stmt.where(Employee.name.ilike(f"%{name}%"))
        count_stmt = count_stmt.where(Employee.name.ilike(f"%{name}%"))
    if status is not None:
        stmt = stmt.where(Employee.status == status)
        count_stmt = count_stmt.where(Employee.status == status)

    stmt = stmt.order_by(Employee.id).offset(offset).limit(limit)
    employees = list(db.scalars(stmt).all())
    total = db.scalar(count_stmt) or 0
    return employees, total


def get_employee(db: Session, employee_id: int) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise NotFoundError(f"El empleado {employee_id} no existe")
    return employee


def _email_taken(db: Session, email: str) -> bool:
    return (
        db.scalar(
            select(func.count()).select_from(Employee).where(Employee.email == email)
        )
        or 0
    ) > 0


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    if _email_taken(db, data.email):
        raise ConflictError(f"El email {data.email} ya está registrado")
    employee = Employee(**data.model_dump())
    db.add(employee)
    db.flush()
    return employee


def update_employee(
    db: Session, employee_id: int, data: EmployeeUpdate
) -> Employee:
    changes = data.model_dump(exclude_unset=True)
    requested_status = changes.pop("status", None)
    # HACK:  se deberia definir si es necesario verificarlo en esta función
    #        - si se activa, descomentar test respectivo
    # if requested_status == "inactive":
    #     raise BusinessRuleError(
    #         "Para desactivar al empleado use DELETE /employees/{id}"
    #     )
    employee = get_employee(db, employee_id)
    new_email = changes.get("email")
    if new_email is not None and new_email != employee.email and _email_taken(db, new_email):
        raise ConflictError(f"El email {new_email} ya está registrado")
    for key, value in changes.items():
        setattr(employee, key, value)
    if requested_status == "active":
        employee.status = "active"
    db.flush()
    return employee


def deactivate_employee(db: Session, employee_id: int) -> tuple[Employee, bool]:
    employee = get_employee(db, employee_id)
    if employee.status == "inactive":
        raise ConflictError(f"El empleado {employee_id} ya está inactivo")
    regla_removida = employee.rule_assignment is not None
    if regla_removida:
        db.delete(employee.rule_assignment)
    employee.status = "inactive"
    db.flush()
    return employee, regla_removida

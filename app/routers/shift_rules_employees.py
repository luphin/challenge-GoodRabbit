from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.shift_rule_employee import (
    ShiftRuleEmployeeCreate,
    ShiftRuleEmployeeRead,
    ShiftRuleEmployeeUpdate,
)
from app.services import assignment_service

router = APIRouter(prefix="/shift-rules-employees", tags=["Asignación de reglas"])


@router.get(
    "", response_model=Page[ShiftRuleEmployeeRead], summary="Listar asignaciones"
)
def list_assignments(
    employee_id: int | None = Query(default=None, description="Filtro por empleado"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    assignments, total = assignment_service.list_assignments(
        db, employee_id=employee_id, limit=limit, offset=offset
    )
    return Page(items=assignments, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=ShiftRuleEmployeeRead,
    status_code=201,
    summary="Asignar regla laboral a un empleado",
)
def create_assignment(
    data: ShiftRuleEmployeeCreate, db: Session = Depends(get_db)
):
    return assignment_service.create_assignment(db, data)


@router.get(
    "/{shift_rule_r_employee_id}",
    response_model=ShiftRuleEmployeeRead,
    summary="Obtener asignación por id",
)
def get_assignment(shift_rule_r_employee_id: int, db: Session = Depends(get_db)):
    return assignment_service.get_assignment(db, shift_rule_r_employee_id)


@router.put(
    "/{shift_rule_r_employee_id}",
    response_model=ShiftRuleEmployeeRead,
    summary="Reemplazar la regla activa de la asignación",
)
def update_assignment(
    shift_rule_r_employee_id: int,
    data: ShiftRuleEmployeeUpdate,
    db: Session = Depends(get_db),
):
    return assignment_service.update_assignment(db, shift_rule_r_employee_id, data)


@router.delete(
    "/{shift_rule_r_employee_id}", status_code=204, summary="Eliminar asignación"
)
def delete_assignment(
    shift_rule_r_employee_id: int, db: Session = Depends(get_db)
) -> None:
    assignment_service.delete_assignment(db, shift_rule_r_employee_id)

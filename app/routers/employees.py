from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeDeactivation,
    EmployeeRead,
    EmployeeUpdate,
)
from app.schemas.report import EmployeeReport
from app.services import employee_service, report_service

router = APIRouter(prefix="/employees", tags=["Empleados"])


@router.get("", response_model=Page[EmployeeRead], summary="Listar empleados")
def list_employees(
    email: str | None = Query(default=None, description="Filtro exacto por email"),
    name: str | None = Query(default=None, description="Búsqueda parcial por nombre"),
    status: Literal["active", "inactive"] | None = Query(
        default=None, description="Filtro por estado"
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    employees, total = employee_service.list_employees(
        db, email=email, name=name, status=status, limit=limit, offset=offset
    )
    return Page(items=employees, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=EmployeeRead,
    status_code=201,
    summary="Crear empleado",
)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    return employee_service.create_employee(db, data)


@router.get("/{employee_id}", response_model=EmployeeRead, summary="Obtener empleado por id")
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return employee_service.get_employee(db, employee_id)


@router.get(
    "/{employee_id}/report",
    response_model=EmployeeReport,
    summary="Reporte del empleado",
)
def get_employee_report(
    employee_id: int,
    report_date: date | None = Query(
        default=None, description="Fecha de referencia (default: hoy)"
    ),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return report_service.build_employee_report(
        db,
        employee_id=employee_id,
        report_date=report_date or date.today(),
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/{employee_id}",
    response_model=EmployeeRead,
    summary="Actualizar empleado (solo campos enviados; usar DELETE para desactivar)",
)
def update_employee(
    employee_id: int, data: EmployeeUpdate, db: Session = Depends(get_db)
):
    return employee_service.update_employee(db, employee_id, data)


@router.delete(
    "/{employee_id}",
    response_model=EmployeeDeactivation,
    response_model_exclude_none=True,
    summary="Desactivar empleado (soft delete)",
)
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    employee, regla_removida = employee_service.deactivate_employee(db, employee_id)
    mensaje = (
        f"El empleado {employee_id} fue desactivado y su regla laboral removida. "
        f"Un empleado inactivo no puede recibir turnos; reactivelo con "
        f"PUT /employees/{employee_id} y status=active."
        if regla_removida
        else f"El empleado {employee_id} fue desactivado. Un empleado inactivo "
        f"no puede recibir turnos; reactivelo con PUT /employees/{employee_id}."
    )
    return EmployeeDeactivation(
        id=employee.id, status=employee.status, regla_removida=regla_removida, mensaje=mensaje
    )

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.schemas.report import EmployeeReport
from app.services import employee_service, report_service

router = APIRouter(prefix="/employees", tags=["Empleados"])


@router.get("", response_model=Page[EmployeeRead], summary="Listar empleados")
def list_employees(
    email: str | None = Query(default=None, description="Filtro exacto por email"),
    name: str | None = Query(default=None, description="Búsqueda parcial por nombre"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    employees, total = employee_service.list_employees(
        db, email=email, name=name, limit=limit, offset=offset
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
    summary="Actualizar empleado (solo campos enviados)",
)
def update_employee(
    employee_id: int, data: EmployeeUpdate, db: Session = Depends(get_db)
):
    return employee_service.update_employee(db, employee_id, data)


@router.delete("/{employee_id}", status_code=204, summary="Eliminar empleado")
def delete_employee(employee_id: int, db: Session = Depends(get_db)) -> None:
    employee_service.delete_employee(db, employee_id)

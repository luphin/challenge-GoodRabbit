from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.shift import (
    ShiftBulkCreated,
    ShiftCreate,
    ShiftRead,
    ShiftUpdate,
)
from app.services import shift_service

router = APIRouter(prefix="/shifts", tags=["Turnos"])


@router.get("", response_model=Page[ShiftRead], summary="Listar turnos")
def list_shifts(
    employee_id: int | None = Query(default=None, description="Filtro por empleado"),
    date_from: date | None = Query(default=None, description="Fecha inicial (inclusiva)"),
    date_to: date | None = Query(default=None, description="Fecha final (inclusiva)"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    shifts, total = shift_service.list_shifts(
        db, employee_id=employee_id, date_from=date_from, date_to=date_to,
        limit=limit, offset=offset,
    )
    return Page(
        items=[ShiftRead.model_validate(s) for s in shifts],
        total=total, limit=limit, offset=offset,
    )


@router.post("", response_model=ShiftRead, status_code=201, summary="Crear turno")
def create_shift(data: ShiftCreate, db: Session = Depends(get_db)):
    return shift_service.create_shift(db, data)


@router.post(
    "/bulk",
    response_model=ShiftBulkCreated,
    status_code=201,
    summary="Carga masiva de turnos (all-or-nothing)",
)
def bulk_create_shifts(body: list[ShiftCreate], db: Session = Depends(get_db)):
    created = shift_service.bulk_create_shifts(db, body)
    return ShiftBulkCreated(
        total=len(created),
        items=[ShiftRead.model_validate(item) for item in created],
    )

@router.get("/{shift_id}", response_model=ShiftRead, summary="Obtener turno por id")
def get_shift(shift_id: int, db: Session = Depends(get_db)):
    return shift_service.get_shift(db, shift_id)


@router.put(
    "/{shift_id}",
    response_model=ShiftRead,
    summary="Actualizar turno (validado contra límites y traslapes)",
)
def update_shift(shift_id: int, data: ShiftUpdate, db: Session = Depends(get_db)):
    return shift_service.update_shift(db, shift_id, data)

# NOTE: se deja como 204 sin mensaje
@router.delete("/{shift_id}", status_code=204, summary="Eliminar turno")
def delete_shift(shift_id: int, db: Session = Depends(get_db)) -> None:
    shift_service.delete_shift(db, shift_id)

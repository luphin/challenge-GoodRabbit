from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.shift_rule import ShiftRuleCreate, ShiftRuleRead, ShiftRuleUpdate
from app.services import shift_rule_service

router = APIRouter(prefix="/shift-rules", tags=["Reglas laborales"])


@router.get("", response_model=Page[ShiftRuleRead], summary="Listar reglas laborales")
def list_shift_rules(
    name: str | None = Query(default=None, description="Búsqueda parcial por nombre"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    rules, total = shift_rule_service.list_shift_rules(
        db, name=name, limit=limit, offset=offset
    )
    return Page(items=rules, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=ShiftRuleRead,
    status_code=201,
    summary="Crear regla laboral",
)
def create_shift_rule(data: ShiftRuleCreate, db: Session = Depends(get_db)):
    return shift_rule_service.create_shift_rule(db, data)


@router.get(
    "/{shift_rule_id}", response_model=ShiftRuleRead, summary="Obtener regla por id"
)
def get_shift_rule(shift_rule_id: int, db: Session = Depends(get_db)):
    return shift_rule_service.get_shift_rule(db, shift_rule_id)


@router.put(
    "/{shift_rule_id}",
    response_model=ShiftRuleRead,
    summary="Actualizar regla (solo campos enviados)",
)
def update_shift_rule(
    shift_rule_id: int, data: ShiftRuleUpdate, db: Session = Depends(get_db)
):
    return shift_rule_service.update_shift_rule(db, shift_rule_id, data)


@router.delete("/{shift_rule_id}", status_code=204, summary="Eliminar regla")
def delete_shift_rule(shift_rule_id: int, db: Session = Depends(get_db)) -> None:
    shift_rule_service.delete_shift_rule(db, shift_rule_id)

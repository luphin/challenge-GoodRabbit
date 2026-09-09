from sqlalchemy import func, select

from app.models import Shift


def _item(employee_id, shift_date, start="08:00", end="16:00"):
    return {
        "employee_id": employee_id,
        "shift_date": shift_date,
        "start_time": start,
        "end_time": end,
    }


def test_bulk_valido_201(client, db_session, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    items = [
        _item(employee.id, "2026-09-07"),
        _item(employee.id, "2026-09-08"),
        _item(employee.id, "2026-09-09"),
    ]
    response = client.post("/shifts/bulk", json=items)
    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3


def test_bulk_all_or_nothing(client, db_session, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    items = [
        _item(employee.id, "2026-09-07"),
        _item(employee.id, "2026-09-08", start="08:00", end="17:00"),
    ]
    response = client.post("/shifts/bulk", json=items)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert len(errors) == 1
    assert errors[0]["index"] == 1
    assert "excede el límite diario" in errors[0]["causa"]
    total = db_session.scalar(select(func.count()).select_from(Shift))
    assert total == 0


def test_bulk_traslape_intra_lote(client, db_session, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    items = [
        _item(employee.id, "2026-09-07", start="08:00", end="16:00"),
        _item(employee.id, "2026-09-07", start="12:00", end="20:00"),
    ]
    response = client.post("/shifts/bulk", json=items)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert errors[0]["index"] == 1
    assert "traslapa" in errors[0]["causa"]


def test_bulk_empleado_inexistente_error_de_item(client, db_session):
    response = client.post("/shifts/bulk", json=[_item(999999, "2026-09-07")])
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert errors[0]["index"] == 0
    assert "no existe" in errors[0]["causa"]


def test_bulk_multiples_errores_acumulados(
    client, db_session, make_employee, make_rule, make_assignment
):
    employee, rule = make_employee(), make_rule(day="5", week="20")
    make_assignment(employee, rule)
    items = [
        _item(employee.id, "2026-09-07", start="08:00", end="15:00"),
        _item(employee.id, "2026-09-08", start="08:00", end="15:00"),
        _item(employee.id, "2026-09-09", start="08:00", end="12:00"),
    ]
    response = client.post("/shifts/bulk", json=items)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert [e["index"] for e in errors] == [0, 1]
    assert errors[0]["causa"].startswith("El empleado")
    assert "excede el límite diario de 5h" in errors[0]["causa"]


def test_bulk_todo_valido_persiste(client, db_session, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    client.post("/shifts/bulk", json=[_item(employee.id, f"2026-09-0{d}") for d in range(1, 6)])
    total = db_session.scalar(select(func.count()).select_from(Shift))
    assert total == 5

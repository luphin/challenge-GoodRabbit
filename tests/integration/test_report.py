def test_reporte_con_metricas(client, make_employee, make_rule, make_assignment, make_shift):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    make_shift(employee.id, shift_date="2026-09-08", start="08:00", end="12:00")
    make_shift(employee.id, shift_date="2026-09-08", start="13:00", end="17:00")
    make_shift(employee.id, shift_date="2026-09-09", start="08:00", end="12:00")

    response = client.get(f"/employees/{employee.id}/report", params={"report_date": "2026-09-08"})
    assert response.status_code == 200
    body = response.json()

    assert body["employee"]["id"] == employee.id
    assert body["shift_rule"]["name"] == "Jornada Completa"
    metrics = body["metrics"]
    assert metrics["daily"]["assigned_hours"] == "8.00"
    assert metrics["daily"]["max_hours"] == "8.00"
    assert metrics["daily"]["usage_percent"] == 100.0
    assert metrics["weekly"]["assigned_hours"] == "12.00"
    assert metrics["weekly"]["max_hours"] == "40.00"
    assert metrics["weekly"]["usage_percent"] == 30.0
    assert metrics["weekly"]["week_start"] == "2026-09-07"
    assert metrics["weekly"]["week_end"] == "2026-09-13"
    assert body["shifts_total"] == 3


def test_reporte_empleado_sin_regla(client, make_employee):
    employee = make_employee()
    response = client.get(f"/employees/{employee.id}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["shift_rule"] is None
    assert body["metrics"] is None


def test_reporte_inexistente_404(client):
    assert client.get("/employees/999999/report").status_code == 404


def test_reporte_filtro_rango_turnos(client, make_employee, make_rule, make_assignment, make_shift):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    make_shift(employee.id, shift_date="2026-09-07")
    make_shift(employee.id, shift_date="2026-09-12")
    response = client.get(
        f"/employees/{employee.id}/report",
        params={"date_from": "2026-09-10", "date_to": "2026-09-14"},
    )
    body = response.json()
    assert body["shifts_total"] == 1
    assert body["shifts"][0]["shift_date"] == "2026-09-12"

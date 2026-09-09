DAY = "2026-09-08"


def _payload(employee_id, shift_date=DAY, start="08:00", end="12:00"):
    return {
        "employee_id": employee_id,
        "shift_date": shift_date,
        "start_time": start,
        "end_time": end,
    }


def _post(client, employee_id, shift_date=DAY, start="08:00", end="12:00"):
    return client.post(
        "/shifts",
        json=_payload(employee_id, shift_date=shift_date, start=start, end=end),
    )


def test_create_valido_201(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    response = _post(client, employee.id)
    assert response.status_code == 201
    assert response.json()["shift_date"] == DAY


def test_create_empleado_sin_regla_422(client, make_employee):
    employee = make_employee()
    response = _post(client, employee.id)
    assert response.status_code == 422
    assert "no tiene una regla laboral" in response.json()["detail"]


def test_create_empleado_inexistente_404(client):
    response = _post(client, 999999)
    assert response.status_code == 404


def test_create_horas_invalidas_422(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    response = _post(client, employee.id, start="10:00", end="10:00")
    assert response.status_code == 422
    assert "mayor a cero" in response.json()["detail"]


def test_create_turno_nocturno_201(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    response = _post(client, employee.id, start="22:00", end="06:00")
    assert response.status_code == 201
    body = response.json()
    assert body["shift_date"] == DAY
    assert body["start_time"] == "22:00:00"
    assert body["end_time"] == "06:00:00"


def test_nocturno_cuenta_al_dia_de_inicio(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    assert _post(client, employee.id, start="22:00", end="06:00").status_code == 201
    response = _post(client, employee.id, start="06:30", end="07:30")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "excede el límite diario de 8h" in detail
    assert "ya tiene 8h asignadas" in detail


def test_traslape_nocturno_con_turno_del_dia_siguiente(
    client, make_employee, make_rule, make_assignment
):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    _post(client, employee.id, start="22:00", end="06:00")
    response = _post(client, employee.id, shift_date="2026-09-09", start="05:00", end="09:00")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "traslapa" in detail
    assert "2026-09-09 05:00" in detail


def test_adyacente_despues_de_nocturno_201(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    _post(client, employee.id, start="22:00", end="06:00")
    response = _post(client, employee.id, shift_date="2026-09-09", start="06:00", end="10:00")
    assert response.status_code == 201


def test_nocturno_largo_traslape_con_manana_siguiente(
    client, make_employee, make_rule, make_assignment
):
    employee, rule = make_employee(), make_rule(day="12", week="40")
    make_assignment(employee, rule)
    assert _post(
        client, employee.id, shift_date="2026-09-07", start="22:00", end="09:00"
    ).status_code == 201
    response = _post(client, employee.id, start="07:00", end="11:00")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "traslapa" in detail
    assert "2026-09-08 09:00" in detail


def test_atribucion_semanal_nocturno_domingo_a_lunes(
    client, make_employee, make_rule, make_assignment
):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    assert _post(
        client, employee.id, shift_date="2026-09-13", start="22:00", end="06:00"
    ).status_code == 201
    fechas = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18"]
    for fecha in fechas:
        response = _post(client, employee.id, shift_date=fecha, start="08:00", end="16:00")
        assert response.status_code == 201, fecha


def test_limite_diario_exacto_201(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    assert _post(client, employee.id).status_code == 201
    response = _post(client, employee.id, start="12:00", end="16:00")
    assert response.status_code == 201


def test_limite_diario_excedido_422_con_causa(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    _post(client, employee.id)
    response = _post(client, employee.id, start="12:00", end="16:30")
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "excede el límite diario" in detail
    assert "excedente: 0.5h" in detail


def test_limite_diario_part_time_5h(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="5", week="20")
    make_assignment(employee, rule)
    assert _post(client, employee.id, start="09:00", end="14:00").status_code == 201
    response = _post(client, employee.id, start="14:00", end="15:00")
    assert response.status_code == 422
    assert "límite diario de 5h" in response.json()["detail"]


def test_limite_semanal_exacto_40h_201(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    fechas = ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]
    for fecha in fechas:
        response = _post(client, employee.id, shift_date=fecha, start="08:00", end="16:00")
        assert response.status_code == 201, fecha


def test_limite_semanal_excedido_422(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    for fecha in ["2026-09-07", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"]:
        _post(client, employee.id, shift_date=fecha, start="08:00", end="16:00")
    response = _post(
        client, employee.id, shift_date="2026-09-12", start="08:00", end="08:30"
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "límite semanal de 40h" in detail
    assert "semana del 2026-09-07 al 2026-09-13" in detail


def test_semana_anterior_no_afecta_la_actual(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    _post(client, employee.id, shift_date="2026-09-06", start="08:00", end="16:00")
    response = _post(client, employee.id, shift_date="2026-09-07", start="08:00", end="16:00")
    assert response.status_code == 201


def test_traslape_422(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    _post(client, employee.id, start="08:00", end="12:00")
    response = _post(client, employee.id, start="11:00", end="13:00")
    assert response.status_code == 422
    assert "traslapa" in response.json()["detail"]


def test_adyacente_no_es_traslape(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    _post(client, employee.id, start="08:00", end="12:00")
    response = _post(client, employee.id, start="12:00", end="16:00")
    assert response.status_code == 201


def test_put_sin_autotraslape_200(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    response = _post(client, employee.id, start="08:00", end="16:00")
    shift_id = response.json()["shift_id"]
    response = client.put(
        f"/shifts/{shift_id}", json={"start_time": "09:00", "end_time": "17:00"}
    )
    assert response.status_code == 200


def test_put_traslape_con_otro_422(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    first_id = _post(client, employee.id, start="08:00", end="12:00").json()["shift_id"]
    _post(client, employee.id, start="14:00", end="18:00")
    response = client.put(
        f"/shifts/{first_id}", json={"start_time": "11:00", "end_time": "15:00"}
    )
    assert response.status_code == 422


def test_put_excede_diario_422(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule(day="8", week="40")
    make_assignment(employee, rule)
    first_id = _post(client, employee.id, start="08:00", end="12:00").json()["shift_id"]
    _post(client, employee.id, start="14:00", end="18:00")
    response = client.put(f"/shifts/{first_id}", json={"end_time": "13:00"})
    assert response.status_code == 422
    assert "excede el límite diario" in response.json()["detail"]


def test_delete_204(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    shift_id = _post(client, employee.id).json()["shift_id"]
    assert client.delete(f"/shifts/{shift_id}").status_code == 204
    assert client.get(f"/shifts/{shift_id}").status_code == 404


def test_get_inexistente_404(client):
    assert client.get("/shifts/999999").status_code == 404


def test_list_filtro_empleado_y_rango(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    _post(client, employee.id, shift_date="2026-09-07")
    _post(client, employee.id, shift_date="2026-09-10")
    response = client.get(
        "/shifts",
        params={
            "employee_id": employee.id,
            "date_from": "2026-09-09",
            "date_to": "2026-09-12",
        },
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["shift_date"] == "2026-09-10"

def test_create_asignacion_valida_201(client, make_employee, make_rule):
    employee, rule = make_employee(), make_rule()
    response = client.post(
        "/shift-rules-employees",
        json={"employee_id": employee.id, "shift_rule_id": rule.shift_rule_id},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == employee.id
    assert body["shift_rule_id"] == rule.shift_rule_id


def test_create_empleado_inexistente_400(client, make_rule):
    rule = make_rule()
    response = client.post(
        "/shift-rules-employees",
        json={"employee_id": 999999, "shift_rule_id": rule.shift_rule_id},
    )
    assert response.status_code == 400
    assert "empleado" in response.json()["detail"]


def test_create_regla_inexistente_400(client, make_employee):
    employee = make_employee()
    response = client.post(
        "/shift-rules-employees",
        json={"employee_id": employee.id, "shift_rule_id": 999999},
    )
    assert response.status_code == 400


def test_create_asignacion_duplicada_409(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    response = client.post(
        "/shift-rules-employees",
        json={"employee_id": employee.id, "shift_rule_id": rule.shift_rule_id},
    )
    assert response.status_code == 409
    assert "ya tiene la regla" in response.json()["detail"]


def test_get_inexistente_404(client):
    assert client.get("/shift-rules-employees/999999").status_code == 404


def test_update_cambia_regla(client, make_employee, make_rule, make_assignment):
    employee, old_rule, new_rule = make_employee(), make_rule(), make_rule(name="Nueva")
    assignment = make_assignment(employee, old_rule)
    response = client.put(
        f"/shift-rules-employees/{assignment.shift_rule_r_employee_id}",
        json={"shift_rule_id": new_rule.shift_rule_id},
    )
    assert response.status_code == 200
    assert response.json()["shift_rule_id"] == new_rule.shift_rule_id


def test_update_regla_inexistente_400(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    assignment = make_assignment(employee, rule)
    response = client.put(
        f"/shift-rules-employees/{assignment.shift_rule_r_employee_id}",
        json={"shift_rule_id": 999999},
    )
    assert response.status_code == 400


def test_delete_204(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    assignment = make_assignment(employee, rule)
    response = client.delete(f"/shift-rules-employees/{assignment.shift_rule_r_employee_id}")
    assert response.status_code == 204


def test_list_filtro_por_empleado(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    assignment = make_assignment(employee, rule)
    response = client.get(
        "/shift-rules-employees", params={"employee_id": employee.id}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["shift_rule_r_employee_id"] == assignment.shift_rule_r_employee_id

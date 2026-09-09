def test_create_regla_valida_201(client):
    response = client.post(
        "/shift-rules",
        json={"name": "Reglatest", "max_hours_day": "8", "max_hours_week": "40"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["shift_rule_id"] > 0
    assert body["max_hours_day"] == "8"


def test_create_semana_menor_que_dia_422(client):
    response = client.post(
        "/shift-rules",
        json={"name": "Inválida", "max_hours_day": "10", "max_hours_week": "5"},
    )
    assert response.status_code == 422
    assert "max_hours_week" in response.text


def test_create_horas_cero_422(client):
    response = client.post(
        "/shift-rules",
        json={"name": "Cero", "max_hours_day": "0", "max_hours_week": "40"},
    )
    assert response.status_code == 422


def test_get_inexistente_404(client):
    assert client.get("/shift-rules/999999").status_code == 404


def test_update_valido(client):
    rule_id = client.post(
        "/shift-rules",
        json={"name": "Editable", "max_hours_day": "6", "max_hours_week": "30"},
    ).json()["shift_rule_id"]
    response = client.put(
        f"/shift-rules/{rule_id}", json={"max_hours_day": "7"}
    )
    assert response.status_code == 200
    assert response.json()["max_hours_day"] == "7"


def test_update_convierte_semana_menor_que_dia_422(client):
    rule_id = client.post(
        "/shift-rules",
        json={"name": "Cruce", "max_hours_day": "4", "max_hours_week": "40"},
    ).json()["shift_rule_id"]
    response = client.put(f"/shift-rules/{rule_id}", json={"max_hours_week": "3"})
    assert response.status_code == 422
    assert "max_hours_week" in response.text


def test_delete_sin_asignaciones_204(client):
    rule_id = client.post(
        "/shift-rules",
        json={"name": "Eliminable", "max_hours_day": "5", "max_hours_week": "20"},
    ).json()["shift_rule_id"]
    assert client.delete(f"/shift-rules/{rule_id}").status_code == 204


def test_delete_con_asignaciones_409(client, make_rule, make_employee, make_assignment):
    rule = make_rule(name="En uso")
    make_assignment(make_employee(), rule)
    response = client.delete(f"/shift-rules/{rule.shift_rule_id}")
    assert response.status_code == 409
    assert "asignada" in response.json()["detail"]


def test_list_filtro_nombre(client, make_rule):
    make_rule(name="Filtrable")
    response = client.get("/shift-rules", params={"name": "filtr"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["name"] == "Filtrable" for item in items)


def test_list_paginado(client, make_rule):
    for i in range(3):
        make_rule(name=f"Regla pag {i}")
    response = client.get("/shift-rules", params={"limit": 2})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 3

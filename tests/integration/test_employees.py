

def test_create_employee_201(client, any_email):
    response = client.post(
        "/employees",
        json={
            "name": "Ana",
            "last_name": "García",
            "phone_number": "+56911112222",
            "email": any_email,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["email"] == any_email


def test_create_email_duplicado_409(client, any_email):
    payload = {
        "name": "Ana",
        "last_name": "García",
        "phone_number": "+56911112222",
        "email": any_email,
    }
    client.post("/employees", json=payload)
    response = client.post("/employees", json=payload)
    assert response.status_code == 409
    assert "ya está registrado" in response.json()["detail"]


def test_create_email_invalido_422(client):
    response = client.post(
        "/employees",
        json={
            "name": "Ana",
            "last_name": "García",
            "phone_number": "+56911112222",
            "email": "no-es-un-email",
        },
    )
    assert response.status_code == 422


def test_get_inexistente_404(client):
    response = client.get("/employees/999999")
    assert response.status_code == 404
    assert "no existe" in response.json()["detail"]


def test_list_paginado(client, make_employee):
    for i in range(3):
        make_employee(name=f"Emp{i}")
    response = client.get("/employees", params={"limit": 2, "offset": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2


def test_list_filtro_nombre(client, make_employee):
    make_employee(name="Zoraida")
    response = client.get("/employees", params={"name": "zor"})
    assert response.status_code == 200
    assert all("Zoraida" == item["name"] for item in response.json()["items"])


def test_update_parcial_solo_cambia_enviado(client, make_employee):
    employee = make_employee(name="Original")
    response = client.put(
        f"/employees/{employee.id}", json={"phone_number": "+56999999999"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["phone_number"] == "+56999999999"
    assert body["name"] == "Original"


def test_update_email_duplicado_409(client, make_employee, any_email):
    make_employee(email=any_email)
    other = make_employee()
    response = client.put(f"/employees/{other.id}", json={"email": any_email})
    assert response.status_code == 409


def test_desactivar_sin_regla_200(client, make_employee):
    employee = make_employee()
    response = client.delete(f"/employees/{employee.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == employee.id
    assert body["status"] == "inactive"
    assert body["regla_removida"] is False
    assert "fue desactivado" in body["mensaje"]
    read = client.get(f"/employees/{employee.id}").json()
    assert read["status"] == "inactive"


def test_desactivar_con_regla_remueve_la_asignacion(
    client, make_employee, make_rule, make_assignment
):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    response = client.delete(f"/employees/{employee.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["regla_removida"] is True
    assert "regla laboral removida" in body["mensaje"]
    remaining = client.get(
        "/shift-rules-employees", params={"employee_id": employee.id}
    ).json()
    assert remaining["total"] == 0


def test_desactivar_dos_veces_409(client, make_employee):
    employee = make_employee()
    assert client.delete(f"/employees/{employee.id}").status_code == 200
    response = client.delete(f"/employees/{employee.id}")
    assert response.status_code == 409
    assert "ya está inactivo" in response.json()["detail"]


def test_empleado_inactivo_no_recibe_turnos(client, make_employee, make_rule, make_assignment):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    assert client.delete(f"/employees/{employee.id}").status_code == 200
    response = client.post(
        "/shifts",
        json={
            "employee_id": employee.id,
            "shift_date": "2026-09-08",
            "start_time": "08:00",
            "end_time": "12:00",
        },
    )
    assert response.status_code == 409
    assert "está inactivo" in response.json()["detail"]


def test_bulk_con_empleado_inactivo_error_de_item(
    client, make_employee, make_rule, make_assignment
):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    client.delete(f"/employees/{employee.id}")
    response = client.post(
        "/shifts/bulk",
        json=[
            {
                "employee_id": employee.id,
                "shift_date": "2026-09-08",
                "start_time": "08:00",
                "end_time": "16:00",
            }
        ],
    )
    assert response.status_code == 422
    assert "está inactivo" in response.json()["detail"][0]["causa"]


def test_reactivar_empleado_conserva_turnos(
    client, make_employee, make_rule, make_assignment, make_shift
):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    make_shift(employee.id)
    client.delete(f"/employees/{employee.id}")
    response = client.put(f"/employees/{employee.id}", json={"status": "active"})
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    shifts = client.get("/shifts", params={"employee_id": employee.id}).json()
    assert shifts["total"] == 1


def test_update_con_status_inactive_redirige(client, make_employee):
    employee = make_employee()
    response = client.put(f"/employees/{employee.id}", json={"status": "inactive"})
    assert response.status_code == 400
    assert "DELETE /employees" in response.json()["detail"]
    assert client.get(f"/employees/{employee.id}").json()["status"] == "active"


def test_desactivar_empleado_con_turnos_conserva_historial(
    client, make_employee, make_rule, make_assignment, make_shift
):
    employee, rule = make_employee(), make_rule()
    make_assignment(employee, rule)
    make_shift(employee.id, shift_date="2026-09-07", start="08:00", end="16:00")
    assert client.delete(f"/employees/{employee.id}").status_code == 200
    shifts = client.get("/shifts", params={"employee_id": employee.id}).json()
    assert shifts["total"] == 1
    report = client.get(f"/employees/{employee.id}/report").json()
    assert report["shifts_total"] == 1
    assert report["shift_rule"] is None
    assert report["metrics"] is None


def test_list_filtro_email(client, make_employee):
    employee = make_employee(name="Único")
    response = client.get("/employees", params={"email": employee.email})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == employee.id


def test_list_filtro_status(client, make_employee):
    active = make_employee(name="Activo")
    inactive = make_employee(name="Inactivo")
    client.delete(f"/employees/{inactive.id}")
    response = client.get("/employees", params={"status": "inactive"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(item["status"] == "inactive" for item in items)
    assert any(item["id"] == inactive.id for item in items)
    response = client.get("/employees", params={"status": "active"})
    assert any(item["id"] == active.id for item in response.json()["items"])
    assert all(item["status"] == "active" for item in response.json()["items"])

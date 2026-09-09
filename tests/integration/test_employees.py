

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


def test_delete_204(client, make_employee):
    employee = make_employee()
    assert client.delete(f"/employees/{employee.id}").status_code == 204
    assert client.get(f"/employees/{employee.id}").status_code == 404


def test_list_filtro_email(client, make_employee):
    employee = make_employee(name="Único")
    response = client.get("/employees", params={"email": employee.email})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == employee.id


def test_delete_con_turnos_409(client, make_employee, make_shift):
    employee = make_employee()
    make_shift(employee_id=employee.id)
    response = client.delete(f"/employees/{employee.id}")
    assert response.status_code == 409
    assert "turnos asignados" in response.json()["detail"]

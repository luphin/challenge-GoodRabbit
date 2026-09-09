def test_health_disponible(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_raiz_disponible(client):
    assert client.get("/").status_code == 200

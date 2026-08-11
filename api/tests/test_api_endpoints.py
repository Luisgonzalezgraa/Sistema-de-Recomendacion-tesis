from io import BytesIO
from uuid import uuid4


def test_health_endpoint_returns_api_status(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["message"] == "API is running"
    assert "version" in payload["data"]


def test_docs_endpoint_lists_core_services(client):
    response = client.get("/api/v1/docs")

    assert response.status_code == 200
    payload = response.get_json()
    endpoints = payload["endpoints"]
    assert endpoints["image_analysis"]["url"] == "/api/v1/analyze/image"
    assert endpoints["hydraulic_analysis"]["method"] == "POST"


def test_image_analysis_requires_file(client):
    response = client.post("/api/v1/analyze/image", data={})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "'file' field is required in multipart/form-data" in payload["errors"]


def test_pump_catalog_endpoint_has_seed_data(client):
    response = client.get("/api/v1/catalog/pumps")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert len(payload["data"]) >= 5
    assert any(pump["model"] == "Honda WB20" for pump in payload["data"])


def test_material_catalog_endpoint_can_filter_by_type(client):
    response = client.get("/api/v1/catalog/materials?type=main_pipe")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert len(payload["data"]) >= 3
    assert all(item["material_type"] == "main_pipe" for item in payload["data"])


def test_material_catalog_accepts_uploaded_photo(client):
    response = client.post(
        "/api/v1/catalog/materials",
        data={
            "material_type": "emitters",
            "name": f"Gotero prueba {uuid4()}",
            "component": "Gotero test 2 L/h",
            "photo": (BytesIO(b"fake image bytes"), "gotero-test.png"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["image_url"].startswith("/uploads/catalog/")


def test_pump_catalog_can_delete_created_pump(client):
    model = f"Bomba prueba {uuid4()}"
    create_response = client.post(
        "/api/v1/catalog/pumps",
        json={
            "model": model,
            "engine_power_hp": 2.0,
            "max_flow_l_min": 120,
            "max_head_m": 18,
        },
    )
    assert create_response.status_code == 201
    pump_id = create_response.get_json()["data"]["id"]

    delete_response = client.delete(f"/api/v1/catalog/pumps/{pump_id}")

    assert delete_response.status_code == 200
    assert delete_response.get_json()["success"] is True


def test_material_catalog_can_delete_created_material(client):
    create_response = client.post(
        "/api/v1/catalog/materials",
        json={
            "material_type": "valves",
            "name": f"Valvula prueba {uuid4()}",
            "component": "Valvula test 32 mm",
        },
    )
    assert create_response.status_code == 201
    material_id = create_response.get_json()["data"]["id"]

    delete_response = client.delete(f"/api/v1/catalog/materials/{material_id}")

    assert delete_response.status_code == 200
    assert delete_response.get_json()["success"] is True

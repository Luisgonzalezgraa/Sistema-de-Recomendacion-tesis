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


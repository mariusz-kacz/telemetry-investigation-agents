from starlette.testclient import TestClient

from telemetry_agents.api.app import create_app


def test_start_investigation() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/investigations",
            json={
                "case_id": "checkout-database-timeout",
            },
        )

    assert response.status_code == 201

    body = response.json()

    assert body

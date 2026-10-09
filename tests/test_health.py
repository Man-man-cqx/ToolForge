"""/health 端点测试。"""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "ToolForge"
    assert body["version"] == "0.1.0"
    assert body["llm_mode"] in {"mock", "openai"}
    assert "server_time" in body

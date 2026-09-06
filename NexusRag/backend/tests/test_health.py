import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient for API integration tests."""
    return TestClient(app)


def test_health_check_returns_200_and_healthy(client: TestClient) -> None:
    """Verify that GET /api/v1/health returns HTTP 200 and exact payload {"status": "healthy"}."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_health_check_content_type(client: TestClient) -> None:
    """Verify that the response Content-Type header is application/json."""
    response = client.get("/api/v1/health")
    assert "application/json" in response.headers.get("content-type", "")


def test_app_operates_without_external_dependencies() -> None:
    """Ensure that the configuration and application load without external API keys or DB instances."""
    settings = get_settings()
    # Confirm default settings do not crash when external services are unconfigured
    assert settings.PROJECT_NAME in ("NexusRAG", "GenWorx RAG")
    assert settings.API_V1_STR == "/api/v1"

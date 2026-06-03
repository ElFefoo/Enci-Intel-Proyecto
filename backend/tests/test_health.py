"""Test básico del endpoint /health."""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

with patch("app.services.firestore_service.get_firestore", return_value=MagicMock()):
    from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "enci-intel-backend"

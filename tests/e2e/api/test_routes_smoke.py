import pytest
from fastapi.testclient import TestClient
from src.presentation.main import app

pytestmark = pytest.mark.e2e


def test_chat_page_renders():
    with TestClient(app) as client:
        response = client.get("/")

        assert response.status_code == 200
        assert "Operasyon Asistanı" in response.text
        assert "tailwindcss" in response.text


def test_dashboard_page_renders():
    with TestClient(app) as client:
        response = client.get("/dashboard")

        assert response.status_code == 200
        assert "Canlı Bildirimler" in response.text
        assert "/notifications/stream" in response.text


def test_orders_explorer_page_renders():
    with TestClient(app) as client:
        response = client.get("/order-tracking")

        assert response.status_code == 200
        assert "Sipariş Takip" in response.text

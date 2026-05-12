import pytest
from fastapi.testclient import TestClient
from src.presentation.main import app

pytestmark = pytest.mark.e2e


def test_chat_page_renders():
    with TestClient(app) as client:
        response = client.get("/")

        assert response.status_code == 200
        assert (
            "Operasyon Asistan\u0131" in response.text
            or "Operasyon Asistan\u00c4\u00b1" in response.text
        )
        assert "tailwindcss" in response.text


def test_dashboard_page_renders():
    with TestClient(app) as client:
        response = client.get("/dashboard")

        assert response.status_code == 200
        assert "Canl\u0131 Bildirimler" in response.text
        assert "Stok ve Envanter" in response.text
        assert "/notifications/stream" in response.text


def test_orders_explorer_page_renders():
    with TestClient(app) as client:
        response = client.get("/order-tracking")

        assert response.status_code == 200
        assert (
            "Sipari\u015f Takip" in response.text
            or "Sipari\u00c5\u0178 Takip" in response.text
        )

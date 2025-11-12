from fastapi.testclient import TestClient
from app import app
import pytest


@pytest.fixture
def client():
    return TestClient(app)


def test_get_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_read_item(client):
    response = client.get("/web/1/?user_name=Lee")
    assert response.status_code == 405


def test_post_item(client):
    response = client.post("/web/1/", data={"user_name": "Lee"})
    assert response.status_code == 200

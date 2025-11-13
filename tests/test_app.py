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

def test_max_players(client,game_ready):
    game_ready.add_player("3","test3")
    game_ready.add_player("4","test4")
    game_ready.add_player("5","test5")
    game_ready.add_player("6","test6")
    game_ready.add_player("7","test7")
    game_ready.add_player("8","test8")
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

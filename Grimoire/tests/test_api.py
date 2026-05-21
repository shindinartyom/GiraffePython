import pytest
from fastapi.testclient import TestClient
from grimoire.main import app

client = TestClient(app)

def test_recommend_user():
    response = client.get("/recommend/Jeeyo")
    assert response.status_code == 200
    data = response.json()
    assert "books" in data
    assert len(data["books"]) > 0

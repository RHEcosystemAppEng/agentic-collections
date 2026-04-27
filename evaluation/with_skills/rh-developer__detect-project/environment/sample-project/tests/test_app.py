import pytest
from app import app


def test_hello():
    with app.test_client() as client:
        r = client.get("/")
        assert r.status_code == 200
        assert b"Hello" in r.data

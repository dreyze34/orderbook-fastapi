import unittest
from fastapi.testclient import TestClient
from app.main import app


class TestHealthHTTP(unittest.TestCase):
    def test_health(self):
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})

    def test_lifespan_resets_storage(self):
        with TestClient(app) as client:
            response = client.post("/orders", json={"side": "buy", "price": "100", "quantity": "5"})
            self.assertEqual(response.status_code, 200)
        with TestClient(app) as client:
            self.assertEqual(client.get("/orders").json(), [])
            response = client.post("/orders", json={"side": "sell", "price": "100", "quantity": "5"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["id"], 1)

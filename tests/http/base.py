"""Client HTTP neuf pour chaque test, avec le vrai lifespan et les services."""
import unittest
from fastapi.testclient import TestClient
from app.main import app


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.client = self.enterContext(TestClient(app))

    def create_order(self, side="buy", price="100", quantity="5"):
        response = self.client.post("/orders", json={"side": side, "price": price, "quantity": quantity})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

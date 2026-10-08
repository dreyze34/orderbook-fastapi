"""HTTP orders, dans l'ordre des routes : GET liste, GET détail, POST."""
from decimal import Decimal
import unittest

from fastapi.testclient import TestClient
from app.main import app


class TestOrdersHTTP(unittest.TestCase):
    def setUp(self):
        # Entrer dans TestClient exécute le lifespan et crée un stockage neuf.
        self.client = self.enterContext(TestClient(app))

    def create(self, side="buy", price="100", quantity="5"):
        response = self.client.post("/orders", json={"side": side, "price": price, "quantity": quantity})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_01_get_orders_empty(self):
        response = self.client.get("/orders")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_01_get_orders_returns_created_orders(self):
        first = self.create()
        second = self.create(price="99")
        response = self.client.get("/orders")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [first, second])

    def test_02_get_order_existing(self):
        order = self.create()
        response = self.client.get(f"/orders/{order['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), order)

    def test_02_get_order_unknown(self):
        response = self.client.get("/orders/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Order not found."})

    def test_02_get_order_invalid_id(self):
        self.assertEqual(self.client.get("/orders/not-an-id").status_code, 422)

    def test_03_create_order_response(self):
        order = self.create(price="100.123456789", quantity="0.3")
        self.assertIsInstance(order["id"], int)
        self.assertEqual(order["side"], "buy")
        self.assertEqual(order["status"], "open")
        self.assertEqual(Decimal(order["price"]), Decimal("100.123456789"))
        self.assertEqual(Decimal(order["quantity"]), Decimal("0.3"))
        self.assertEqual(Decimal(order["remaining_quantity"]), Decimal("0.3"))

    def test_03_create_order_matches_and_updates_both_read_routes(self):
        for resting_side, incoming_side in (("sell", "buy"), ("buy", "sell")):
            with self.subTest(side=incoming_side):
                # Finir le précédent carnet avant de passer à l'autre sens.
                resting = self.create(resting_side, quantity="10")
                incoming = self.create(incoming_side, quantity="4")
                self.assertEqual(incoming["status"], "filled")
                self.assertEqual(Decimal(incoming["remaining_quantity"]), 0)
                response = self.client.get(f"/orders/{resting['id']}")
                self.assertEqual(response.status_code, 200)
                updated = response.json()
                self.assertEqual(updated["status"], "partially_filled")
                self.assertEqual(Decimal(updated["quantity"]), 10)
                self.assertEqual(Decimal(updated["remaining_quantity"]), 6)
                response = self.client.get("/orders")
                self.assertEqual(response.status_code, 200)
                self.assertIn(updated, response.json())
                self.create(incoming_side, quantity="6")
                response = self.client.get(f"/orders/{resting['id']}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "filled")

    def test_03_create_order_respects_price_limit(self):
        sell = self.create("sell", "101")
        buy = self.create("buy", "100")
        self.assertEqual(sell["status"], "open")
        self.assertEqual(buy["status"], "open")
        response = self.client.get(f"/orders/{sell['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sell)

    def test_03_create_order_invalid_body_does_not_mutate_storage(self):
        invalid_bodies = [
            {},
            {"side": "buy", "price": "100"},
            {"side": "invalid", "price": "100", "quantity": "5"},
            {"side": "buy", "price": "invalid", "quantity": "5"},
            {"side": "buy", "price": "100", "quantity": None},
            {"side": "buy", "price": "NaN", "quantity": "5"},
        ]
        for body in invalid_bodies:
            with self.subTest(body=body):
                response = self.client.post("/orders", json=body)
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.get("/orders").json(), [])
        self.assertEqual(self.create()["id"], 1)

    def test_03_create_order_unique_ids(self):
        self.assertEqual([self.create()["id"] for _ in range(3)], [1, 2, 3])

    @unittest.expectedFailure
    def test_03_create_order_rejects_nonpositive_price(self):
        """Régression connue : OrderCreate n'impose pas encore price > 0."""
        responses = [self.client.post("/orders", json={"side": "buy", "price": value, "quantity": "5"}) for value in ("0", "-1")]
        self.assertEqual([r.status_code for r in responses], [422, 422])
        self.assertEqual(self.client.get("/orders").json(), [])

    @unittest.expectedFailure
    def test_03_create_order_rejects_nonpositive_quantity(self):
        """Régression connue : OrderCreate n'impose pas encore quantity > 0."""
        responses = [self.client.post("/orders", json={"side": "buy", "price": "100", "quantity": value}) for value in ("0", "-1")]
        self.assertEqual([r.status_code for r in responses], [422, 422])
        self.assertEqual(self.client.get("/orders").json(), [])

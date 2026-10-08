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
        self.assertEqual(response.json(), {"detail": "Order 999 not found."})

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

    def test_03_create_order_rejects_nonpositive_price(self):
        """Un prix nul ou négatif doit être refusé."""
        responses = [self.client.post("/orders", json={"side": "buy", "price": value, "quantity": "5"}) for value in ("0", "-1")]
        self.assertEqual([r.status_code for r in responses], [422, 422])
        self.assertEqual(self.client.get("/orders").json(), [])

    def test_03_create_order_rejects_nonpositive_quantity(self):
        """Une quantité nulle ou négative doit être refusée."""
        responses = [self.client.post("/orders", json={"side": "buy", "price": "100", "quantity": value}) for value in ("0", "-1")]
        self.assertEqual([r.status_code for r in responses], [422, 422])
        self.assertEqual(self.client.get("/orders").json(), [])

    def test_04_cancel_open_order(self):
        for side in ("buy", "sell"):
            with self.subTest(side=side):
                order = self.create(side)
                response = self.client.patch(f"/orders/{order['id']}")
                self.assertEqual(response.status_code, 200, response.text)
                cancelled = response.json()
                self.assertEqual(cancelled, {**order, "status": "cancelled"})
                self.assertEqual(self.client.get(f"/orders/{order['id']}").json(), cancelled)

    def test_04_cancel_partial_order_preserves_trade(self):
        sell = self.create("sell", quantity="5")
        self.create("buy", quantity="2")
        before = self.client.get("/trades").json()
        response = self.client.patch(f"/orders/{sell['id']}")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertEqual(Decimal(response.json()["remaining_quantity"]), 3)
        self.assertEqual(self.client.get("/trades").json(), before)
        incoming = self.create("buy", quantity="3")
        self.assertEqual(incoming["status"], "open")

    def test_04_cancel_unknown_order(self):
        response = self.client.patch("/orders/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Order 999 not found."})

    def test_04_cancel_invalid_id(self):
        self.assertEqual(self.client.patch("/orders/not-an-id").status_code, 422)

    def test_04_cancel_filled_order(self):
        sell = self.create("sell")
        self.create("buy")
        before = self.client.get(f"/orders/{sell['id']}").json()
        response = self.client.patch(f"/orders/{sell['id']}")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": f"Order {sell['id']} is already filled or canceled."})
        self.assertEqual(self.client.get(f"/orders/{sell['id']}").json(), before)

    def test_04_cancel_already_cancelled_order(self):
        order = self.create()
        url = f"/orders/{order['id']}"
        self.assertEqual(self.client.patch(url).status_code, 200)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(url).json()["status"], "cancelled")

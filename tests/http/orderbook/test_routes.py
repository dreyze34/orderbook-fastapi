from decimal import Decimal
from tests.http.base import APITestCase


class TestOrderBookHTTP(APITestCase):
    def book(self):
        response = self.client.get("/orderbook")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_01_get_orderbook_empty(self):
        self.assertEqual(self.book(), {"bids": {}, "asks": {}})

    def test_01_get_orderbook_price_levels_and_fifo(self):
        first = self.create_order("buy", "100", "2")
        second = self.create_order("buy", "100", "3")
        sell = self.create_order("sell", "101", "4")
        book = self.book()
        self.assertEqual([o["id"] for o in book["bids"]["100"]], [first["id"], second["id"]])
        self.assertEqual(book["asks"]["101"][0]["id"], sell["id"])

    def test_01_get_orderbook_decimal_price_and_quantity(self):
        order = self.create_order("buy", "100.25", "0.3")
        book = self.book()
        self.assertEqual(set(book["bids"]), {"100.25"})
        resting = book["bids"]["100.25"][0]
        self.assertEqual(resting["id"], order["id"])
        self.assertEqual(Decimal(resting["remaining_quantity"]), Decimal("0.3"))

    def test_01_get_orderbook_after_matching(self):
        self.create_order("sell", quantity="5")
        self.create_order("buy", quantity="2")
        book = self.book()
        self.assertEqual(book["bids"], {})
        self.assertEqual(Decimal(book["asks"]["100"][0]["remaining_quantity"]), 3)
        self.assertEqual(book["asks"]["100"][0]["status"], "partially_filled")
        self.create_order("buy", quantity="3")
        self.assertEqual(self.book(), {"bids": {}, "asks": {}})

    def test_01_get_orderbook_after_cancellation(self):
        order = self.create_order()
        self.assertEqual(self.client.patch(f"/orders/{order['id']}").status_code, 200)
        self.assertEqual(self.book(), {"bids": {}, "asks": {}})

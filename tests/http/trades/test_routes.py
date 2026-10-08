from decimal import Decimal
from tests.http.base import APITestCase


class TestTradesHTTP(APITestCase):
    def match(self):
        sell = self.create_order("sell", "100.25", "0.3")
        buy = self.create_order("buy", "101", "0.1")
        return sell, buy

    def test_01_get_trades_empty(self):
        response = self.client.get("/trades")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_01_get_trades_after_matching(self):
        sell, buy = self.match()
        response = self.client.get("/trades")
        self.assertEqual(response.status_code, 200, response.text)
        trades = response.json()
        self.assertEqual(len(trades), 1)
        self.assertEqual(set(trades[0]), {"id", "buy_order_id", "sell_order_id", "price", "quantity"})
        self.assertEqual((trades[0]["sell_order_id"], trades[0]["buy_order_id"]), (sell["id"], buy["id"]))
        self.assertEqual(Decimal(trades[0]["price"]), Decimal("100.25"))
        self.assertEqual(Decimal(trades[0]["quantity"]), Decimal("0.1"))

    def test_01_get_trades_multiple_executions(self):
        self.create_order("sell", quantity="2")
        self.create_order("sell", quantity="3")
        self.create_order("buy", quantity="5")
        response = self.client.get("/trades")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([t["id"] for t in response.json()], [1, 2])
        self.assertEqual([Decimal(t["quantity"]) for t in response.json()], [2, 3])

    def test_02_get_trade_existing(self):
        self.match()
        response = self.client.get("/trades/1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), self.client.get("/trades").json()[0])

    def test_02_get_trade_unknown(self):
        response = self.client.get("/trades/999")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Trade 999 not found."})

    def test_02_get_trade_invalid_id(self):
        self.assertEqual(self.client.get("/trades/not-an-id").status_code, 422)

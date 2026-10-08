"""Tests du carnet : .venv/bin/python -m unittest discover -s tests -v."""

import unittest

from app.models.orderbook import OrderBook
from app.models.order import Order, Side, OrderStatus
from decimal import Decimal


def make_order(order_id, side, price, quantity):
    return Order(
        id=order_id,
        side=Side(side.lower()),
        price=Decimal(price),
        quantity=Decimal(quantity),
        remaining_quantity=Decimal(quantity),
    )


class TestOrderBook(unittest.TestCase):
    def assert_consistent(self, book):
        """Chaque ordre actif appartient à un seul niveau non vide."""
        active = {}
        for side, levels in ((Side.BUY, book.bids), (Side.SELL, book.asks)):
            for price, queue in levels.items():
                self.assertTrue(queue, "Un niveau vide doit être supprimé")
                for order in queue:
                    self.assertEqual(order.side, side)
                    self.assertEqual(order.price, price)
                    self.assertGreater(order.remaining_quantity, 0)
                    self.assertNotIn(order.id, active)
                    active[order.id] = order
        if book.bids and book.asks:
            self.assertLess(book.best_bid(), book.best_ask())

    def assert_trade(self, trade, buy_id, sell_id, price, quantity):
        self.assertEqual(trade["buy_order_id"], buy_id)
        self.assertEqual(trade["sell_order_id"], sell_id)
        self.assertEqual(trade["price"], price)
        self.assertEqual(trade["quantity"], quantity)

    def test_empty_book(self):
        book = OrderBook()
        self.assertIsNone(book.best_bid())
        self.assertIsNone(book.best_ask())

    def test_insert_orders_and_best_prices(self):
        book = OrderBook()
        orders = [
            make_order(1, "BUY", 99, 2),
            make_order(2, "BUY", 100, 3),
            make_order(3, "BUY", 100, 4),
            make_order(4, "SELL", 103, 5),
            make_order(5, "SELL", 102, 6),
            make_order(6, "SELL", 102, 7),
        ]
        for order in orders:
            self.assertEqual(book.add_order(order), [])
        self.assertEqual(book.best_bid(), 100)
        self.assertEqual(book.best_ask(), 102)
        self.assertEqual([o.id for o in book.bids[100]], [2, 3])
        self.assertEqual([o.id for o in book.asks[102]], [5, 6])
        self.assert_consistent(book)

    def test_exact_fill_at_resting_price(self):
        for incoming_side, resting_side, limit in (
            ("BUY", "SELL", 105),
            ("SELL", "BUY", 95),
        ):
            with self.subTest(side=incoming_side):
                book = OrderBook()
                resting = make_order(1, resting_side, 100, 5)
                incoming = make_order(2, incoming_side, limit, 5)
                book.add_order(resting)
                trades = book.add_order(incoming)
                self.assertEqual(len(trades), 1)
                buy_id, sell_id = (2, 1) if incoming_side == "BUY" else (1, 2)
                self.assert_trade(trades[0], buy_id, sell_id, 100, 5)
                self.assertEqual(resting.remaining_quantity, 0)
                self.assertEqual(resting.status, OrderStatus.FILLED)
                self.assertEqual(incoming.remaining_quantity, 0)
                self.assertEqual(incoming.status, OrderStatus.FILLED)
                self.assertIsNone(book.best_bid())
                self.assertIsNone(book.best_ask())
                self.assert_consistent(book)

    def test_partial_fill_keeps_resting_order(self):
        for incoming_side, resting_side in (("BUY", "SELL"), ("SELL", "BUY")):
            with self.subTest(side=incoming_side):
                book = OrderBook()
                resting = make_order(1, resting_side, 100, 10)
                incoming = make_order(2, incoming_side, 100, 4)
                book.add_order(resting)
                trades = book.add_order(incoming)
                self.assertEqual(len(trades), 1)
                self.assertEqual(trades[0]["quantity"], 4)
                self.assertEqual(resting.remaining_quantity, 6)
                self.assertEqual(resting.status, OrderStatus.PARTIALLY_FILLED)
                self.assertEqual(incoming.remaining_quantity, 0)
                self.assertEqual(incoming.status, OrderStatus.FILLED)
                levels = book.asks if resting_side == "SELL" else book.bids
                self.assertIs(levels[100][0], resting)
                self.assert_consistent(book)

    def test_incoming_remainder_is_inserted(self):
        for incoming_side, resting_side in (("BUY", "SELL"), ("SELL", "BUY")):
            with self.subTest(side=incoming_side):
                book = OrderBook()
                book.add_order(make_order(1, resting_side, 100, 3))
                incoming = make_order(2, incoming_side, 100, 8)
                trades = book.add_order(incoming)
                self.assertEqual(len(trades), 1)
                self.assertEqual(trades[0]["quantity"], 3)
                self.assertEqual(incoming.remaining_quantity, 5)
                self.assertEqual(incoming.status, OrderStatus.PARTIALLY_FILLED)
                levels = book.bids if incoming_side == "BUY" else book.asks
                self.assertIs(levels[100][0], incoming)
                self.assert_consistent(book)

    def test_fifo_within_price_level(self):
        for incoming_side, resting_side in (("BUY", "SELL"), ("SELL", "BUY")):
            with self.subTest(side=incoming_side):
                book = OrderBook()
                # Les identifiants ne déterminent pas la priorité temporelle.
                first = make_order(20, resting_side, 100, 3)
                second = make_order(10, resting_side, 100, 4)
                book.add_order(first)
                book.add_order(second)
                incoming = make_order(30, incoming_side, 100, 5)
                trades = book.add_order(incoming)
                resting_ids = [
                    t["sell_order_id"] if incoming_side == "BUY" else t["buy_order_id"]
                    for t in trades
                ]
                self.assertEqual(resting_ids, [20, 10])
                self.assertEqual([t["quantity"] for t in trades], [3, 2])
                self.assertEqual(second.remaining_quantity, 2)
                self.assert_consistent(book)

    def test_price_priority_and_limit_across_levels(self):
        for incoming_side, resting_side, prices, limit in (
            ("BUY", "SELL", [99, 100, 101], 100),
            ("SELL", "BUY", [101, 100, 99], 100),
        ):
            with self.subTest(side=incoming_side):
                book = OrderBook()
                # Insérer le moins bon prix en premier pour vérifier la priorité prix.
                for index in (2, 1, 0):
                    book.add_order(make_order(index + 1, resting_side, prices[index], 2))
                incoming = make_order(4, incoming_side, limit, 7)
                trades = book.add_order(incoming)
                self.assertEqual([t["price"] for t in trades], prices[:2])
                self.assertEqual([t["quantity"] for t in trades], [2, 2])
                self.assertEqual(incoming.remaining_quantity, 3)
                levels = book.asks if resting_side == "SELL" else book.bids
                self.assertEqual(levels[Decimal(prices[2])][0].remaining_quantity, 2)
                self.assert_consistent(book)


if __name__ == "__main__":
    unittest.main()

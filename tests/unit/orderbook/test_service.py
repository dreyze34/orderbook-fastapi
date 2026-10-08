from decimal import Decimal
import unittest
from app.models.order import Side
from app.services.order_service import OrderService
from app.services.orderbook_service import OrderBookService
from app.storage.memory import InMemoryStorage


class TestOrderBookService(unittest.TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.orders = OrderService(self.storage)
        self.service = OrderBookService(self.storage)

    def test_01_get_orderbook_empty(self):
        book = self.service.get_orderbook()
        self.assertEqual(book.bids, {})
        self.assertEqual(book.asks, {})

    def test_01_get_orderbook_shares_orders_storage(self):
        order = self.orders.place_order(Decimal("100.25"), Side.BUY, Decimal("5"))
        book = self.service.get_orderbook()
        self.assertEqual(book.bids[Decimal("100.25")][0], order)
        self.orders.cancel_order(order.id)
        self.assertEqual(self.service.get_orderbook().bids, {})

    def test_01_get_orderbook_after_partial_and_full_matching(self):
        sell = self.orders.place_order(Decimal("100"), Side.SELL, Decimal("5"))
        self.orders.place_order(Decimal("100"), Side.BUY, Decimal("2"))
        book = self.service.get_orderbook()
        self.assertEqual(book.asks[Decimal("100")][0].remaining_quantity, Decimal("3"))
        self.orders.place_order(Decimal("100"), Side.BUY, Decimal("3"))
        self.assertEqual(self.service.get_orderbook().asks, {})
        self.assertEqual(sell.remaining_quantity, 0)

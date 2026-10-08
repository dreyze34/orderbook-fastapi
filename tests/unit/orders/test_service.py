"""Service orders : lecture de liste, lecture individuelle, création, annulation."""
from decimal import Decimal
import unittest

from app.models.order import Side, OrderStatus
from app.services.order_service import OrderService
from app.storage.memory import InMemoryStorage


class TestOrderService(unittest.TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.service = OrderService(self.storage)

    def place(self, side=Side.BUY, price="100", quantity="5"):
        return self.service.place_order(Decimal(price), side, Decimal(quantity))

    def test_01_get_orders_empty(self):
        self.assertEqual(list(self.service.get_orders()), [])

    def test_01_get_orders_includes_filled_and_cancelled(self):
        sell = self.place(Side.SELL)
        buy = self.place()
        cancelled = self.place(price="90")
        self.service.cancel_order(cancelled.id)
        orders = list(self.service.get_orders())
        self.assertEqual([o.id for o in orders], [sell.id, buy.id, cancelled.id])
        self.assertEqual([o.status for o in orders], [OrderStatus.FILLED, OrderStatus.FILLED, OrderStatus.CANCELLED])

    def test_02_get_order_unknown(self):
        self.assertIsNone(self.service.get_order(999))

    def test_02_get_order_existing(self):
        order = self.place()
        self.assertEqual(self.service.get_order(order.id), order)

    def test_03_place_order_preserves_decimal_precision_and_initial_quantity(self):
        sell = self.place(Side.SELL, "100.123456789", "0.3")
        buy = self.place(Side.BUY, "101", "0.1")
        self.assertEqual(sell.quantity, Decimal("0.3"))
        self.assertEqual(sell.remaining_quantity, Decimal("0.2"))
        self.assertEqual(sell.status, OrderStatus.PARTIALLY_FILLED)
        self.assertEqual(buy.status, OrderStatus.FILLED)
        trade = next(iter(self.storage.trades.values()))
        self.assertEqual((trade.buy_order_id, trade.sell_order_id), (buy.id, sell.id))
        self.assertEqual(trade.price, Decimal("100.123456789"))
        self.assertEqual(trade.quantity, Decimal("0.1"))

    def test_03_place_orders_generates_distinct_order_and_trade_ids(self):
        self.place(Side.SELL, quantity="2")
        self.place(Side.SELL, quantity="3")
        buy = self.place(quantity="5")
        self.assertEqual(set(self.storage.orders), {1, 2, 3})
        self.assertEqual(set(self.storage.trades), {1, 2})
        self.assertEqual([t.id for t in self.storage.trades.values()], [1, 2])
        self.assertTrue(all(t.buy_order_id == buy.id for t in self.storage.trades.values()))

    def test_04_cancel_order_unknown(self):
        self.assertIsNone(self.service.cancel_order(999))

    def test_04_cancel_open_order_removes_it_from_matching(self):
        for side in (Side.BUY, Side.SELL):
            with self.subTest(side=side):
                self.setUp()
                cancelled = self.place(side)
                self.assertEqual(self.service.cancel_order(cancelled.id), cancelled)
                self.assertEqual(cancelled.status, OrderStatus.CANCELLED)
                incoming = self.place(Side.SELL if side == Side.BUY else Side.BUY)
                self.assertEqual(incoming.status, OrderStatus.OPEN)
                self.assertEqual(self.storage.trades, {})

    def test_04_cancel_partial_order_preserves_executed_trades(self):
        sell = self.place(Side.SELL)
        self.place(quantity="2")
        self.service.cancel_order(sell.id)
        self.assertEqual(sell.status, OrderStatus.CANCELLED)
        self.assertEqual(sell.remaining_quantity, Decimal("3"))
        self.assertFalse(self.storage.orderbook.asks)
        self.assertEqual(len(self.storage.trades), 1)

    def test_04_cancel_filled_order_does_not_change_status(self):
        sell = self.place(Side.SELL)
        self.place()
        self.service.cancel_order(sell.id)
        self.assertEqual(sell.status, OrderStatus.FILLED)

    def test_04_cancel_order_twice_is_idempotent(self):
        order = self.place()
        self.service.cancel_order(order.id)
        self.service.cancel_order(order.id)
        self.assertEqual(order.status, OrderStatus.CANCELLED)
        self.assertFalse(self.storage.orderbook.bids)

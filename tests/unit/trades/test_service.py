from decimal import Decimal
import unittest
from app.exceptions import TradeNotFoundError
from app.models.order import Side
from app.services.order_service import OrderService
from app.services.trade_service import TradeService
from app.storage.memory import InMemoryStorage


class TestTradeService(unittest.TestCase):
    def setUp(self):
        self.storage = InMemoryStorage()
        self.orders = OrderService(self.storage)
        self.service = TradeService(self.storage)

    def match(self):
        sell = self.orders.place_order(Decimal("100.25"), Side.SELL, Decimal("0.3"))
        buy = self.orders.place_order(Decimal("101"), Side.BUY, Decimal("0.1"))
        return sell, buy

    def test_01_get_trades_empty(self):
        self.assertEqual(list(self.service.get_trades()), [])

    def test_01_get_trades_created_by_matching(self):
        sell, buy = self.match()
        trades = list(self.service.get_trades())
        self.assertEqual(len(trades), 1)
        trade = trades[0]
        self.assertEqual((trade.id, trade.sell_order_id, trade.buy_order_id), (1, sell.id, buy.id))
        self.assertEqual((trade.price, trade.quantity), (Decimal("100.25"), Decimal("0.1")))

    def test_01_get_trades_preserved_after_cancellation(self):
        sell, _ = self.match()
        before = list(self.service.get_trades())
        self.orders.cancel_order(sell.id)
        self.assertEqual(list(self.service.get_trades()), before)

    def test_02_get_trade_returns_instance(self):
        self.match()
        self.assertIs(self.service.get_trade(1), self.storage.trades[1])

    def test_02_get_trade_unknown(self):
        with self.assertRaises(TradeNotFoundError) as ctx:
            self.service.get_trade(999)
        self.assertEqual(ctx.exception.trade_id, 999)
        self.assertEqual(self.storage.trades, {})

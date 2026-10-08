from itertools import count
from threading import Lock

from typing import List, Dict, Deque
from app.models.order import Order
from app.models.trade import Trade
from app.models.orderbook import OrderBook

class InMemoryStorage:

    def __init__(self):
        self.orderbook: OrderBook = OrderBook()

        self.trades: Dict[int, Trade] = {}
        self.orders: Dict[int, Order] = {}

        self.order_id_counter = count(1)
        self.trade_id_counter = count(1)

        self.lock = Lock()

    def next_order_id(self) -> int:
        return next(self.order_id_counter)

    def next_trade_id(self) -> int:
        return next(self.trade_id_counter)
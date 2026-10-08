from typing import List, Dict
from collections import deque
import time

from app.schemas.schemas import OrderCreate, OrderResponse
from app.services.dataclasses import Order, Trade

class OrderBook:
    def __init__(self, symbol: str):
        self.symbol: str = symbol
        self.bids: Dict[int, List[Order]] = {}
        self.asks: Dict[int, List[Order]] = {}
        self.orders: Dict[int, Order] = {}

    def best_bid(self) -> int:
        if not self.bids:
            return None
        
        return max(self.bids)

    def best_ask(self) -> int:
        if not self.asks:
            return None

        return min(self.asks)

    def add_order(self, order: Order) -> List[Trade]:
        trades = self._match(order)
        if order.quantity > 0:
            if order.side == "BUY":
                if order.price not in self.bids:
                    self.bids[order.price] = deque()
                self.bids[order.price].append(order)
                self.orders[order.order_id] = order
            else:
                if order.price not in self.asks:
                    self.asks[order.price] = deque()
                self.asks[order.price].append(order)
                self.orders[order.order_id] = order
        return trades

    def _match(self, order: Order) -> List[Trade]:
        trades = []
        if order.side == "BUY":
            best_ask = self.best_ask()
            while (
                order.quantity > 0
                and best_ask is not None
                and best_ask <= order.price
            ):
                sell_order = self.asks[best_ask][0]

                quantity_executed = min(order.quantity, sell_order.quantity)

                order.quantity -= quantity_executed
                sell_order.quantity -= quantity_executed
                if sell_order.quantity == 0:
                    self.asks[best_ask].popleft()
                    if not self.asks[best_ask]:
                        del self.asks[best_ask]
                        best_ask = self.best_ask()
                    del self.orders[sell_order.order_id]
                
                trade = Trade(
                    buy_order_id=order.order_id,
                    sell_order_id=sell_order.order_id,
                    price_executed=sell_order.price,
                    quantity_executed=quantity_executed,
                    timestamp=int(time.time())
                )
                trades.append(trade)

        elif order.side == "SELL":
            best_bid = self.best_bid()
            while (
                order.quantity > 0
                and best_bid is not None
                and best_bid >= order.price
            ):
                buy_order = self.bids[best_bid][0]

                quantity_executed = min(order.quantity, buy_order.quantity)

                order.quantity -= quantity_executed
                buy_order.quantity -= quantity_executed
                if buy_order.quantity == 0:
                    self.bids[best_bid].popleft()
                    if not self.bids[best_bid]:
                        del self.bids[best_bid]
                        best_bid = self.best_bid()
                    del self.orders[buy_order.order_id]
                
                trade = Trade(
                    buy_order_id=buy_order.order_id,
                    sell_order_id=order.order_id,
                    price_executed=buy_order.price,
                    quantity_executed=quantity_executed,
                    timestamp=int(time.time())
                )
                trades.append(trade)
        return trades
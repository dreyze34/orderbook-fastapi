from typing import List, Dict, Deque
from collections import deque

from app.models.order import Order, Side, OrderStatus


class OrderBook:

    def __init__(self):
        self.bids: Dict[int, Deque[Order]] = {}
        self.asks: Dict[int, Deque[Order]] = {}

    def best_bid(self) -> int:
        return max(self.bids) if self.bids else None
    
    def best_ask(self) -> int:
        return min(self.asks) if self.asks else None

    def add_order(self, order: Order) -> List[Dict]:
        trades = []
        if order.side == Side.BUY:
            best_ask = self.best_ask()
            while (
                order.remaining_quantity > 0
                and best_ask is not None
                and best_ask <= order.price
            ):
                sell_order = self.asks[best_ask][0]

                quantity_executed = min(order.remaining_quantity, sell_order.remaining_quantity)

                order.remaining_quantity -= quantity_executed
                sell_order.remaining_quantity -= quantity_executed

                if sell_order.remaining_quantity == 0:
                    sell_order.status = OrderStatus.FILLED
                    self.asks[best_ask].popleft()
                    if not self.asks[best_ask]:
                        del self.asks[best_ask]
                        best_ask = self.best_ask()
                else:
                    sell_order.status = OrderStatus.PARTIALLY_FILLED
                
                trade = {
                    "buy_order_id": order.id,
                    "sell_order_id": sell_order.id,
                    "price": sell_order.price,
                    "quantity": quantity_executed,
                }
                trades.append(trade)

            if order.remaining_quantity == 0:
                order.status = OrderStatus.FILLED
            else:
                if order.remaining_quantity < order.quantity:
                    order.status = OrderStatus.PARTIALLY_FILLED
                self.bids.setdefault(order.price, deque()).append(order)

        elif order.side == Side.SELL:
            best_bid = self.best_bid()
            while (
                order.remaining_quantity > 0
                and best_bid is not None
                and best_bid >= order.price
            ):
                buy_order = self.bids[best_bid][0]

                quantity_executed = min(order.remaining_quantity, buy_order.remaining_quantity)

                order.remaining_quantity -= quantity_executed
                buy_order.remaining_quantity -= quantity_executed

                if buy_order.remaining_quantity == 0:
                    buy_order.status = OrderStatus.FILLED
                    self.bids[best_bid].popleft()
                    if not self.bids[best_bid]:
                        del self.bids[best_bid]
                        best_bid = self.best_bid()
                else:
                    buy_order.status = OrderStatus.PARTIALLY_FILLED
                
                trade = {
                    "buy_order_id": buy_order.id,
                    "sell_order_id": order.id,
                    "price": buy_order.price,
                    "quantity": quantity_executed,
                }
                trades.append(trade)

            if order.remaining_quantity == 0:
                order.status = OrderStatus.FILLED
            else:
                if order.remaining_quantity < order.quantity:
                    order.status = OrderStatus.PARTIALLY_FILLED
                self.asks.setdefault(order.price, deque()).append(order)

        return trades

    def cancel_order(self, order: Order):
        if order.side == Side.BUY:
            for bid, sub_orders in self.bids.items():
                if order in sub_orders:
                    sub_orders.remove(order)
                    if not sub_orders:
                        del self.bids[bid]
                    return
        elif order.side == Side.SELL:
            for ask, sub_orders in self.asks.items():
                if order in sub_orders:
                    sub_orders.remove(order)
                    if not sub_orders:
                        del self.asks[ask]
                    return
        return
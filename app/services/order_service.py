from typing import List

from app.models.order import Order, OrderStatus
from app.models.trade import Trade
from app.storage.memory import InMemoryStorage
from app.exceptions import OrderNotCancellableError, OrderNotFoundError


class OrderService:

    def __init__(self, storage: InMemoryStorage):
        self.storage: InMemoryStorage = storage

    def place_order(self, price, side, quantity) -> Order:
        with self.storage.lock:
            order_id = self.storage.next_order_id()
            order = Order(
                id=order_id,
                side=side,
                price=price,
                quantity=quantity,
                remaining_quantity=quantity
            )

            trades = self.storage.orderbook.add_order(order)

            for trade_dict in trades:
                trade_id = self.storage.next_trade_id()
                trade = Trade(
                    **trade_dict,
                    id=trade_id
                )
                self.storage.trades[trade_id] = trade

            self.storage.orders[order.id] = order

        return order

    def cancel_order(self, order_id: int) -> Order | None:
        with self.storage.lock:
            order = self.storage.orders.get(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
            
            if order.status == OrderStatus.FILLED or order.status == OrderStatus.CANCELLED:
                raise OrderNotCancellableError(order_id)
            
            order.status = OrderStatus.CANCELLED
            self.storage.orderbook.cancel_order(order)
        return order

    def get_order(self, order_id: int) -> Order:
        with self.storage.lock:
            order = self.storage.orders.get(order_id)
            if not order:
                raise OrderNotFoundError(order_id)
        return order

    def get_orders(self) -> List[Order]:
        with self.storage.lock:
            orders = self.storage.orders.values()
        return orders
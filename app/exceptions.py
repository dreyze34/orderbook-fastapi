class OrderNotFoundError(Exception):
    def __init__(self, order_id: int):
        self.order_id = order_id
        super().__init__(f"Order {order_id} not found.")

class OrderNotCancellableError(Exception):
    def __init__(self, order_id: int):
        super().__init__(f"Order {order_id} is already filled or canceled.")

class TradeNotFoundError(Exception):
    def __init__(self, trade_id: int):
        self.trade_id = trade_id
        super().__init__(f"Trade {trade_id} not found.")
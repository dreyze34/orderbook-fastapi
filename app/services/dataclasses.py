from dataclasses import dataclass
from typing import Literal


@dataclass
class Order:
    order_id: int
    symbol: str
    side: Literal["BUY", "SELL"]
    price: int
    quantity: int
    timestamp: int

@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price_executed: int
    quantity_executed: int
    timestamp: int
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"

@dataclass
class Order:
    id: str
    side: Side
    price: Decimal
    quantity: Decimal
    remaining_quantity: Decimal
    status: OrderStatus = OrderStatus.OPEN
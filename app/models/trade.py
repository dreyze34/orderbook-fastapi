from dataclasses import dataclass
from typing import Literal
from decimal import Decimal


@dataclass
class Trade:
    id: int
    buy_order_id: str
    sell_order_id: str
    price: Decimal
    quantity: Decimal
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from decimal import Decimal

class TradeResponse(BaseModel):
    id: int
    buy_order_id: int
    sell_order_id: int
    price: Decimal
    quantity: Decimal
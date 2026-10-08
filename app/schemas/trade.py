from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from decimal import Decimal

class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buy_order_id: int
    sell_order_id: int
    price: Decimal
    quantity: Decimal
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class OrderCreate(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    price: int
    quantity: int

class OrderResponse(OrderCreate):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    timestamp: int

class Trade(BaseModel):
    buy_order_id: int
    sell_order_id: int
    price_executed: int
    quantity_executed: int
    timestamp: int
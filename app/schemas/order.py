from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

from app.models.order import Side, OrderStatus

class OrderCreate(BaseModel):
    side: Side
    price: Decimal = Field(gt=0)
    quantity: Decimal = Field(gt=0)

class OrderResponse(OrderCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    side: Side
    remaining_quantity: Decimal
    status: OrderStatus
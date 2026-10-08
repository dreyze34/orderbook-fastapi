from pydantic import BaseModel
from decimal import Decimal

from typing import Dict, List

from app.schemas.order import OrderResponse

class OrderBookResponse(BaseModel):
    bids: Dict[Decimal, List[OrderResponse]]
    asks: Dict[Decimal, List[OrderResponse]]

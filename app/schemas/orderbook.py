from pydantic import BaseModel

from typing import Dict, List

from app.models.order import Order

class OrderBookResponse(BaseModel):
    bids: Dict[int, List[Order]]
    asks: Dict[int, List[Order]]
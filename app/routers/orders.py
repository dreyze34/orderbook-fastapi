from typing import List, Dict
import time

from fastapi import APIRouter, Request, Depends, HTTPException

from app.dependencies import get_orderbooks
from app.schemas.schemas import OrderResponse, OrderCreate
from app.services.orderbooks import OrderBook
from app.services.dataclasses import Order

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

@router.get("/symbol/{symbol}", response_model=list[OrderResponse])
def get_orders(
    symbol: str,
    orderbooks: Dict[str, OrderBook] = Depends(get_orderbooks)
):
    book = orderbooks.get(symbol)
    if book is None:
        raise HTTPException(status_code=404, detail="Unknown symbol.")
    return list(book.orders.values())

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    orderbooks: Dict[str, OrderBook] = Depends(get_orderbooks)
):
    for book in orderbooks.values():
        order = book.orders.get(order_id)
        if order is not None:
            return order

    raise HTTPException(status_code=404, detail="Order not found.")

@router.post("", response_model=OrderResponse)
async def create_order(
    request: Request,
    order_create: OrderCreate,
    orderbooks: Dict[str, OrderBook] = Depends(get_orderbooks),
) -> OrderResponse:
    book = orderbooks.get(order_create.symbol)
    if book is None:
        raise HTTPException(status_code=422, detail="Unknown symbol.")

    next_id = request.app.state.next_id
    order = Order(
        **order_create.model_dump(),
        order_id=next_id,
        timestamp=int(time.time())
    )
    book.add_order(order)
    request.app.state.next_id += 1

    response = OrderResponse.model_validate(order)
    
    return response
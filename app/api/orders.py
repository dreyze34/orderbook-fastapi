from typing import List, Dict, Annotated
import time

from fastapi import APIRouter, Request, Depends, HTTPException

from app.services.order_service import OrderService
from app.dependencies import get_order_service

from app.schemas.order import OrderResponse, OrderCreate

from app.exceptions import OrderNotCancellableError, OrderNotFoundError

ServiceDep = Annotated[OrderService, Depends(get_order_service)]

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)

@router.get("", response_model=list[OrderResponse])
def get_orders(
    service: ServiceDep
):
    orders = service.get_orders()
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    service: ServiceDep
):
    try:
        return service.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )

@router.post("", response_model=OrderResponse)
async def create_order(
    order: OrderCreate,
    service: ServiceDep
):
    return service.place_order(
        price=order.price,
        side=order.side,
        quantity=order.quantity
    )

@router.patch("/{order_id}", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    service: ServiceDep
):
    try:
        return service.cancel_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )
    except OrderNotCancellableError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc)
        )
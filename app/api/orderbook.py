from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.orderbook import OrderBookResponse

from app.services.orderbook_service import OrderBookService

from app.dependencies import get_orderbook_service

router = APIRouter(
    prefix="/orderbook",
    tags=["orderbook"]
)

ServiceDep = Annotated[OrderBookService, Depends(get_orderbook_service)]

@router.get("", response_model=OrderBookResponse)
def get_orberbook(
    service: ServiceDep
):
    return service.get_orderbook()

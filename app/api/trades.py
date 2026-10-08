from typing import List, Dict, Annotated
import time

from fastapi import APIRouter, Request, Depends, HTTPException

from app.services.trade_service import TradeService
from app.dependencies import get_trade_service

from app.schemas.trade import TradeResponse

from app.exceptions import TradeNotFoundError

ServiceDep = Annotated[TradeService, Depends(get_trade_service)]

router = APIRouter(
    prefix="/trades",
    tags=["trades"]
)

@router.get("", response_model=list[TradeResponse])
def get_trades(
    service: ServiceDep
):
    return service.get_trades()

@router.get("/{trade_id}", response_model=TradeResponse)
def get_trade(
    trade_id: int,
    service: ServiceDep
):
    try:
        return service.get_trade(trade_id)
    except TradeNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))



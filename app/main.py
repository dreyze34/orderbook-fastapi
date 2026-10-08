from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.storage.memory import InMemoryStorage

from app.services.order_service import OrderService
from app.services.trade_service import TradeService
from app.services.orderbook_service import OrderBookService

from app.api import orders, trades, orderbook

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = InMemoryStorage()
    app.state.order_service = OrderService(storage)
    app.state.trade_service = TradeService(storage)
    app.state.orderbook_service = OrderBookService(storage)
    yield

app = FastAPI(title="Orderbook API", version="0.1.0", lifespan=lifespan)

app.include_router(orders.router)
app.include_router(trades.router)
app.include_router(orderbook.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
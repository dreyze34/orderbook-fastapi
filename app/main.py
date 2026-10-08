from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.services.orderbooks import OrderBook

from app.routers import orders

symbols = ["BTCUSD", "ETHUSD", "SOLUSD"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    orderbooks = {symbol: OrderBook(symbol) for symbol in symbols}
    next_id = 0
    app.state.orderbooks = orderbooks
    app.state.next_id = next_id
    yield

app = FastAPI(title="Orderbook API", version="0.1.0", lifespan=lifespan)

app.include_router(orders.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
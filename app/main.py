from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.storage.memory import InMemoryStorage
from app.services.order_service import OrderService

from app.api import orders

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = InMemoryStorage()
    app.state.order_service = OrderService(storage)
    yield

app = FastAPI(title="Orderbook API", version="0.1.0", lifespan=lifespan)

app.include_router(orders.router)

@app.get("/health")
async def health():
    return {"status": "ok"}
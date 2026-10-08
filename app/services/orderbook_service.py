from app.storage.memory import InMemoryStorage

class OrderBookService:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def get_orderbook(self):
        return self.storage.orderbook
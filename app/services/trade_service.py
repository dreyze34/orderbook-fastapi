from typing import List

from app.models.trade import Trade

from app.storage.memory import InMemoryStorage

from app.exceptions import TradeNotFoundError

class TradeService:
    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def get_trade(self, trade_id: int) -> Trade:
        with self.storage.lock:
            trade = self.storage.trades.get(trade_id)
            if not trade:
                raise TradeNotFoundError(trade_id)

        return trade

    def get_trades(self) -> List[Trade]:
        with self.storage.lock:
            return self.storage.trades.values()

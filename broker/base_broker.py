from abc import ABC, abstractmethod

class BrokerBase(ABC):
    @abstractmethod
    def place_order(self, symbol, qty, side, price, order_type="market", **kwargs) -> dict:
        pass

class BrokerFactory:
    @staticmethod
    def get_broker(name: str, **kwargs):
        if name == "alpaca":
            from broker.alpaca_broker import AlpacaBroker
            return AlpacaBroker(**kwargs)
        elif name == "kraken":
            from broker.kraken_broker import KrakenBroker
            return KrakenBroker(**kwargs)
        else:
            raise ValueError(f"Unknown broker: {name}")
from broker.base_broker import BrokerBase
import logging
from utilities.logging import setup_logging

class AlpacaBroker(BrokerBase):
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://paper-api.alpaca.markets"):
        from alpaca.trading.client import TradingClient
        self.client = TradingClient(api_key, api_secret, paper=True)
        self.logger = setup_logging('AlpacaBroker', logging.DEBUG)

    def get_account(self):
        account = self.client.get_account()
        return account

    def get_positions(self):
        positions = self.client.get_all_positions()
        return positions

    def place_order(self, symbol: str, qty: int, side: str, price: str,
                     type: str = "market", time_in_force: str = "gtc"):
        order = self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            price=price,
            time_in_force=time_in_force
        )
        self.logger.debug(f"Placed order: {order}")
        return order

    def get_order(self, order_id: str):
        order = self.client.get_order_by_id(order_id)
        return order

    def cancel_order(self, order_id: str):
        self.client.cancel_order(order_id)
        self.logger.debug(f"Cancelled order ID: {order_id}")
import ccxt
import logging

logger = logging.getLogger(__name__)


class TradeExecutor:
    def __init__(self, api_key, api_secret):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
        })

    def execute_trade(self, symbol, side, amount):
        try:
            order = self.exchange.create_order(symbol, 'market', side, amount)
            logger.info(f"Executed trade: {order}")
            return order
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    def get_active_orders(self):
        try:
            orders = self.exchange.fetch_open_orders()
            logger.info(f"Fetched active orders: {orders}")
            return orders
        except Exception as e:
            logger.error(f"Error fetching active orders: {e}")
            return []

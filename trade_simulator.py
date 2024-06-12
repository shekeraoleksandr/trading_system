import logging
import pandas as pd

logger = logging.getLogger(__name__)

class TradeSimulator:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.positions = []

    def execute_trade(self, symbol, side, amount, price):
        trade = {
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'timestamp': pd.Timestamp.now()
        }
        self.positions.append(trade)
        if side == 'buy':
            self.balance -= amount * price
        elif side == 'sell':
            self.balance += amount * price

        logger.info(f"Executed simulated trade: {trade}")
        logger.info(f"Updated balance: {self.balance}")

    def get_balance(self):
        logger.info(f"Current balance: {self.balance}")
        return self.balance

    def get_positions(self):
        logger.info(f"Current positions: {self.positions}")
        return self.positions

    def get_active_orders(self):
        active_orders = [pos for pos in self.positions if pos['side'] == 'buy' or pos['side'] == 'sell']
        logger.info(f"Active orders: {active_orders}")
        return active_orders

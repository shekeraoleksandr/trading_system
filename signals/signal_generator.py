import numpy as np
from telegram import Bot
import asyncio


class SignalGenerator:
    def __init__(self, signals, telegram_token, telegram_chat_id, trade_executor, trade_simulator, trade_amount,
                 dry_run):
        self.signals = signals
        self.bot = Bot(token=telegram_token)
        self.chat_id = telegram_chat_id
        self.trade_executor = trade_executor
        self.trade_simulator = trade_simulator
        self.trade_amount = trade_amount
        self.dry_run = dry_run

        # Додавання колонки 'position'
        self.signals['position'] = 0

    def generate_trade_signals(self):
        # Логіка для визначення сигналів
        self.signals['position'] = np.where(
            self.signals['short_mavg'] > self.signals['long_mavg'], 1, 0
        )
        self.signals['position'] = np.where(
            self.signals['short_mavg'] < self.signals['long_mavg'], -1, self.signals['position']
        )

        trade_signals = self.signals[self.signals['position'] != 0].copy()
        return trade_signals

    async def send_alert_async(self, message):
        await self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_alert(self, signal):
        trade_type = 'BUY' if signal['position'] == 1.0 else 'SELL'
        message = f"Alert: {signal.name} - {trade_type} at price {signal['close']}"
        print(message)  # Для відображення у консолі

        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.send_alert_async(message))

    def execute_trade(self, signal):
        trade_type = 'BUY' if signal['position'] == 1.0 else 'SELL'
        price = signal['close']
        amount = self.trade_amount / price  # Розрахунок кількості на основі ціни і розміру торгівлі

        if self.dry_run:
            self.trade_simulator.execute_trade('BTC/USDT', trade_type, amount, price)
        else:
            order = self.trade_executor.execute_trade('BTC/USDT', trade_type, amount)
            if order:
                print(f"Trade executed: {order}")
            else:
                print("Trade execution failed")

    def process_signals(self):
        trade_signals = self.generate_trade_signals()
        for index, signal in trade_signals.iterrows():
            self.send_alert(signal)
            self.execute_trade(signal)

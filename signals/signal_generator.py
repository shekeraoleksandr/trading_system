from telegram import Bot
import asyncio


class SignalGenerator:
    def __init__(self, signals, telegram_token, telegram_chat_id):
        self.signals = signals
        self.bot = Bot(token=telegram_token)
        self.chat_id = telegram_chat_id

    def generate_trade_signals(self):
        trade_signals = self.signals[self.signals['position'] != 0].copy()
        return trade_signals

    async def send_alert_async(self, message):
        await self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_alert(self, signal):
        trade_type = 'BUY' if signal['position'] == 1.0 else 'SELL'
        message = f"Alert: {signal['date']} - {trade_type} at price {signal['price']}"
        print(message)  # Для відображення у консолі

        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.send_alert_async(message))

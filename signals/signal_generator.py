class SignalGenerator:
    def __init__(self, signals):
        self.signals = signals

    def generate_trade_signals(self):
        trade_signals = self.signals[self.signals['position'] != 0].copy()
        return trade_signals

    @staticmethod
    def send_alert(signal):
        trade_type = 'BUY' if signal['position'] == 1.0 else 'SELL'
        print(f"Alert: {signal['date']} - {trade_type} at price {signal['price']}")


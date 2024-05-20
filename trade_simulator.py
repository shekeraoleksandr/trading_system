class TradeSimulator:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.positions = []
        self.trades = []

    def execute_trade(self, symbol, trade_type, amount, price):
        trade = {
            'symbol': symbol,
            'type': trade_type,
            'amount': amount,
            'price': price,
            'total': amount * price
        }

        if trade_type.upper() == 'BUY':
            if self.balance >= trade['total']:
                self.positions.append(trade)
                self.balance -= trade['total']
                self.trades.append(trade)
                print(f"Simulated BUY: {amount} {symbol} at {price}")
            else:
                print("Insufficient balance for simulated BUY")
        elif trade_type.upper() == 'SELL':
            for position in self.positions:
                if position['amount'] >= amount:
                    position['amount'] -= amount
                    self.balance += trade['total']
                    self.trades.append(trade)
                    print(f"Simulated SELL: {amount} {symbol} at {price}")
                    break
            else:
                print("Insufficient position for simulated SELL")

    def get_balance(self):
        return self.balance

    def get_positions(self):
        return self.positions

    def get_trades(self):
        return self.trades

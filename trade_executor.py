import ccxt


class TradeExecutor:
    def __init__(self, api_key, api_secret):
        self.exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

    def execute_trade(self, symbol, trade_type, amount):
        try:
            if trade_type.upper() == 'BUY':
                order = self.exchange.create_market_buy_order(symbol, amount)
            elif trade_type.upper() == 'SELL':
                order = self.exchange.create_market_sell_order(symbol, amount)
            else:
                raise ValueError(f"Invalid trade type: {trade_type}")
            return order
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None

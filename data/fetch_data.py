import ccxt
import pandas as pd


class DataFetcher:
    def __init__(self):
        self.exchange = ccxt.binance()

    def fetch_ohlcv(self, symbol, timeframe, since, until):
        all_data = []
        while since < until:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            if not ohlcv:
                break
            last_timestamp = ohlcv[-1][0]
            since = last_timestamp + 1
            all_data.extend(ohlcv)
        data = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        return data

import ccxt
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    def __init__(self):
        self.exchange = ccxt.binance()

    def fetch_ohlcv(self, symbol, timeframe, since, until):
        all_data = []
        while since < until:
            try:
                data = self.exchange.fetch_ohlcv(symbol, timeframe, since)
                if not data:
                    break
                df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                all_data.append(df)
                since = data[-1][0] + 1  # Move to the next timestamp after the last one retrieved
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                break
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    def fetch_market_state(self, symbol):
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': ticker['symbol'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'last': ticker['last'],
                'timestamp': ticker['timestamp']
            }
        except Exception as e:
            logger.error(f"Error fetching market state: {e}")
            return {}

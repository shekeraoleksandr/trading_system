import pandas as pd


class TechnicalIndicators:
    @staticmethod
    def moving_average(data, period=20):
        data[f'MA_{period}'] = data['close'].rolling(window=period).mean()
        return data

    @staticmethod
    def rsi(data, period=14):
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        data[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        return data

    @staticmethod
    def macd(data, short_period=12, long_period=26, signal_period=9):
        short_ema = data['close'].ewm(span=short_period, adjust=False).mean()
        long_ema = data['close'].ewm(span=long_period, adjust=False).mean()
        data['MACD'] = short_ema - long_ema
        data['Signal_Line'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
        return data

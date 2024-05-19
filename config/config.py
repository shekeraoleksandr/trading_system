class Config:
    BINANCE_SYMBOL = 'BTC/USDT'
    TIMEFRAME = '1d'
    SINCE = '2020-01-01T00:00:00Z'  # Початок періоду
    UNTIL = '2024-01-01T00:00:00Z'  # Кінець періоду
    DB_NAME = 'trading_data.db'
    TRADE_SIZE = 0.2  # 20% від капіталу
    MAX_OPEN_TRADES = 5  # Максимум 5 одночасних угод

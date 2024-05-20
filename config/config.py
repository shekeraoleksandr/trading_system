import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BINANCE_SYMBOL = 'BTC/USDT'
    TIMEFRAME = '1d'
    SINCE = '2023-01-01T00:00:00Z'  # Початок періоду
    UNTIL = '2024-01-01T00:00:00Z'  # Кінець періоду
    TRADE_SIZE = 0.2  # 20% від капіталу
    MAX_OPEN_TRADES = 5  # Максимум 5 одночасних угод
    TELEGRAM_TOKEN = '6701796848:AAE3Ppo_3Yfr7iSAyyLdZFKjuTIciakkk3s'
    TELEGRAM_CHAT_ID = '423651665'
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
    DRY_RUN = True  # Режим dry_run для використання віртуальних грошей

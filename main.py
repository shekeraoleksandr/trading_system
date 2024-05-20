import pandas as pd

from data import DataFetcher, DataSaver, DataLoader
from analysis import TechnicalIndicators
from backtesting import Backtest
from signals import SignalGenerator
from visualization import Plotter
from config import Config


def main():
    # Ініціалізація конфігурації
    config = Config()

    # Ініціалізація класів для отримання, збереження та завантаження даних
    fetcher = DataFetcher()
    saver = DataSaver(config.DB_NAME)
    loader = DataLoader(config.DB_NAME)

    # Отримання даних
    data = fetcher.fetch_ohlcv(config.BINANCE_SYMBOL, config.TIMEFRAME, fetcher.exchange.parse8601(config.SINCE),
                               fetcher.exchange.parse8601(config.UNTIL))
    if data.empty:
        print("No data fetched. Exiting.")
        return

    # Виведення перших і останніх рядків даних
    print("First few rows of data:")
    print(data.head())
    print("Last few rows of data:")
    print(data.tail())

    # Збереження даних
    table_name = f"{config.BINANCE_SYMBOL.replace('/', '_')}_{config.TIMEFRAME}"
    saver.save_to_db(data, table_name)
    print(f"Дані успішно збережені в таблиці {table_name}")

    # Завантаження даних
    data = loader.load_data(table_name)
    print(f"Завантажено {len(data)} рядків даних")

    # Перетворення timestamp на datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'])

    # Встановлення timestamp як індекс
    data.set_index('timestamp', inplace=True)

    # Ініціалізація класу для технічного аналізу
    indicators = TechnicalIndicators()

    # Обчислення технічних індикаторів
    data = indicators.moving_average(data, period=20)
    data = indicators.rsi(data, period=14)
    data = indicators.macd(data)

    # Виведення результатів
    print(data.head())

    # Ініціалізація бектестера з backtrader
    backtest = Backtest(initial_capital=10000.0)

    # Запуск бектестингу з backtrader
    backtest.run(data, config.TRADE_SIZE, config.MAX_OPEN_TRADES)

    # Отримання позицій зі стратегії
    positions = backtest.get_positions()

    # Ініціалізація генератора сигналів
    signal_generator = SignalGenerator(positions)

    # Генерація торгових сигналів
    trade_signals = signal_generator.generate_trade_signals()
    # print(trade_signals)

    # Надсилання сповіщень
    for index, signal in trade_signals.iterrows():
        signal_generator.send_alert(signal)

    # Візуалізація даних
    plotter = Plotter()
    plotter.plot_data(data, config.BINANCE_SYMBOL)


if __name__ == "__main__":
    main()

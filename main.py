import sys
import os
import numpy as np
import pandas as pd
import argparse
import time
import asyncio
from backtesting import Backtest
from visualization import Plotter
from telegram import Bot
from data import DataFetcher, DataSaver, DataLoader
from analysis import TechnicalIndicators
from signals import SignalGenerator
from config import Config
from trade_executor import TradeExecutor
from trade_simulator import TradeSimulator
from telegram_bot import TelegramBot


def format_date(date_str):
    return pd.to_datetime(date_str).strftime('%Y%m%d')


def run_backtest(config, interval, since, until):
    db_path = "sqlite:///db/trading_data.db"
    if not os.path.exists("db"):
        os.makedirs("db")

    fetcher = DataFetcher()
    saver = DataSaver(db_path)
    loader = DataLoader(db_path)

    formatted_since = format_date(since)
    formatted_until = format_date(until)
    table_name = f"{config.BINANCE_SYMBOL.replace('/', '_')}_{interval}_{formatted_since}_{formatted_until}"

    # Check for existing data in the database
    data = loader.load_data(table_name)
    if data.empty:
        print("No data found in database. Fetching new data...")
        data = fetcher.fetch_ohlcv(config.BINANCE_SYMBOL, interval, fetcher.exchange.parse8601(since),
                                   fetcher.exchange.parse8601(until))
        if data.empty:
            print("No data fetched. Exiting.")
            return
        saver.save_to_db(data, table_name)
        print(f"Data successfully saved to table {table_name}")
    else:
        print(f"Loaded {len(data)} rows of data from database")

    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)

    indicators = TechnicalIndicators()
    data = indicators.moving_average(data, period=20)
    data = indicators.rsi(data, period=14)
    data = indicators.macd(data)

    print(data.head())

    initial_capital = 10000.0
    backtest = Backtest(initial_capital=initial_capital)
    backtest.run(data, config.TRADE_SIZE, config.MAX_OPEN_TRADES)
    positions = backtest.get_positions()

    ending_balance = backtest.get_portfolio_value()
    profit_percentage = (ending_balance - initial_capital) / initial_capital * 100
    total_trades = backtest.get_total_trades()
    winning_trades = backtest.get_winning_trades()
    losing_trades = backtest.get_losing_trades()

    message = (
        f"Backtest completed successfully.\n\n"
        f"Interval: {interval}\n"
        f"Period: {since} to {until}\n"
        f"Initial Balance: ${initial_capital:,.2f}\n"
        f"Ending Balance: ${ending_balance:,.2f}\n"
        f"Profit: {profit_percentage:.2f}%\n"
        f"Total Trades: {total_trades}\n"
        f"Winning Trades: {winning_trades}\n"
        f"Losing Trades: {losing_trades}"
    )

    print(message)

    telegram_bot = TelegramBot(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    asyncio.run(telegram_bot.send_message(message))

    plotter = Plotter()
    plotter.plot_data(data, config.BINANCE_SYMBOL)


def run_dry_run(config, interval):
    fetcher = DataFetcher()
    trade_executor = TradeExecutor(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
    trade_simulator = TradeSimulator(initial_balance=10000.0)

    telegram_bot = TelegramBot(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    asyncio.run(telegram_bot.send_message(f"Dry run trading started with interval {interval}."))

    while True:
        data = fetcher.fetch_ohlcv(config.BINANCE_SYMBOL, interval, fetcher.exchange.milliseconds() - 86400000,
                                   fetcher.exchange.milliseconds())
        if data.empty:
            print("No data fetched. Waiting for new data...")
            time.sleep(60)  # Adjust the sleep interval according to the timeframe
            continue

        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('timestamp', inplace=True)

        indicators = TechnicalIndicators()
        data = indicators.moving_average(data, period=20)
        data = indicators.rsi(data, period=14)
        data = indicators.macd(data)

        # Ensure 'short_mavg' and 'long_mavg' are present in the data
        if 'short_mavg' not in data.columns or 'long_mavg' not in data.columns:
            print("Missing moving average columns. Skipping this iteration.")
            time.sleep(60)
            continue

        signal_generator = SignalGenerator(data, config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, trade_executor,
                                           trade_simulator, config.TRADE_SIZE, config.DRY_RUN)
        signal_generator.process_signals()

        print(f"Sleeping for {interval} interval...")
        time.sleep(60)  # Adjust the sleep interval according to the timeframe


def main():
    parser = argparse.ArgumentParser(description='Trading System')
    parser.add_argument('mode', choices=['backtest', 'dry_run'], help='Mode to run the trading system')
    parser.add_argument('interval', nargs='?', default=None,
                        help='Time interval for the candlesticks (e.g., 15m, 1h, 1d)')
    parser.add_argument('since', nargs='?', default=None, help='Start date for fetching historical data (YYYY-MM-DD)')
    parser.add_argument('until', nargs='?', default=None, help='End date for fetching historical data (YYYY-MM-DD)')

    args = parser.parse_args()

    config = Config()

    interval = args.interval if args.interval else config.TIMEFRAME
    since = args.since if args.since else config.SINCE
    until = args.until if args.until else config.UNTIL

    if args.mode == 'backtest':
        run_backtest(config, interval, since, until)
    elif args.mode == 'dry_run':
        run_dry_run(config, interval)


if __name__ == "__main__":
    main()

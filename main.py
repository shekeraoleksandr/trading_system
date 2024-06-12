import os
import pandas as pd
import argparse
import time
import asyncio
import logging

from backtesting import Backtest
from visualization import Plotter
from data import DataFetcher, DataSaver, DataLoader
from analysis import TechnicalIndicators
from signals import SignalGenerator
from config import Config
from trade_executor import TradeExecutor
from trade_simulator import TradeSimulator
from telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='trading_system.log')
logger = logging.getLogger(__name__)


def format_date(date_str):
    return pd.to_datetime(date_str).strftime('%Y%m%d')


def get_sleep_interval(interval):
    units = {
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    if interval[-1] in units:
        return int(interval[:-1]) * units[interval[-1]]
    return 60  # default to 60 seconds if interval is not recognized


def run_backtest(config, interval, since, until):
    db_path = "db/trading_data.db"
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
        logger.info("No data found in database. Fetching new data...")
        since_timestamp = fetcher.exchange.parse8601(since + "T00:00:00Z")
        until_timestamp = fetcher.exchange.parse8601(until + "T00:00:00Z")
        data = fetcher.fetch_ohlcv(config.BINANCE_SYMBOL, interval, since_timestamp, until_timestamp)
        if data.empty:
            logger.error("No data fetched. Exiting.")
            return
        saver.save_to_db(data, table_name)
        logger.info(f"Data successfully saved to table {table_name}")
    else:
        logger.info(f"Loaded {len(data)} rows of data from database")

    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)

    indicators = TechnicalIndicators()
    data = indicators.moving_average(data, period=20)
    data = indicators.rsi(data, period=14)
    data = indicators.macd(data)

    logger.info(data.head())

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

    telegram_bot = TelegramBot(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    asyncio.run(telegram_bot.send_message(message))

    logger.info(message)

    plotter = Plotter()
    plotter.plot_data(data, config.BINANCE_SYMBOL)


def run_dry_run(config, interval):
    fetcher = DataFetcher()
    trade_executor = TradeExecutor(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
    trade_simulator = TradeSimulator(initial_balance=10000.0)

    telegram_bot = TelegramBot(config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID)
    asyncio.run(telegram_bot.send_message(f"Dry run trading started with interval {interval}."))

    sleep_interval = get_sleep_interval(interval)

    while True:
        data = fetcher.fetch_ohlcv(config.BINANCE_SYMBOL, interval, fetcher.exchange.milliseconds() - 86400000,
                                   fetcher.exchange.milliseconds())
        if data.empty:
            logger.warning("No data fetched. Waiting for new data...")
            time.sleep(sleep_interval)
            continue

        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('timestamp', inplace=True)

        indicators = TechnicalIndicators()
        data = indicators.moving_average(data, period=20)
        data = indicators.rsi(data, period=14)
        data = indicators.macd(data)

        if 'short_mavg' not in data.columns or 'long_mavg' not in data.columns:
            logger.error("Missing moving average columns. Skipping this iteration.")
            time.sleep(sleep_interval)
            continue

        signal_generator = SignalGenerator(data, config.TELEGRAM_TOKEN, config.TELEGRAM_CHAT_ID, trade_executor,
                                           trade_simulator, config.TRADE_SIZE, config.DRY_RUN)
        signal_generator.process_signals()

        # Логування активних ордерів та стану ринку
        active_orders = trade_executor.get_active_orders()
        market_state = fetcher.fetch_market_state(config.BINANCE_SYMBOL)

        logger.info(f"Active orders: {active_orders}")
        logger.info(f"Market state: {market_state}")

        logger.info(f"Sleeping for {sleep_interval} seconds...")
        time.sleep(sleep_interval)


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

    logger.info(f"Starting system in {args.mode} mode with interval {interval}")

    if args.mode == 'backtest':
        run_backtest(config, interval, since, until)
    elif args.mode == 'dry_run':
        run_dry_run(config, interval)


if __name__ == "__main__":
    main()
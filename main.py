import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import asyncio
import logging
from datetime import datetime
from backtesting import Backtest
from visualization import Plotter
from data import DataFetcher, DataSaver, DataLoader
from analysis import TechnicalIndicators
from signals import SignalGenerator
from trade_executor import TradeExecutor
from trade_simulator import TradeSimulator
from telegram_bot import TelegramBot
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='trading_system.log')
logger = logging.getLogger(__name__)


class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading System")

        self.config = Config()

        self.create_widgets()

    def create_widgets(self):
        # Buttons
        self.start_button = tk.Button(self.root, text="Start Trading", command=self.start_trading)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop Trading", command=self.stop_trading)
        self.stop_button.pack(pady=10)

        self.results_button = tk.Button(self.root, text="Show Results", command=self.show_results)
        self.results_button.pack(pady=10)

        self.backtest_button = tk.Button(self.root, text="Run Backtest", command=self.run_backtest)
        self.backtest_button.pack(pady=10)

        # Combobox for interval selection
        self.interval_label = tk.Label(self.root, text="Select Interval:")
        self.interval_label.pack(pady=5)

        self.interval_var = tk.StringVar()
        self.interval_combobox = ttk.Combobox(self.root, textvariable=self.interval_var)
        self.interval_combobox['values'] = ("1m", "5m", "15m", "30m", "1h", "4h", "1d")
        self.interval_combobox.pack(pady=5)
        self.interval_combobox.current(6)  # Set default value to "1d"

        # Entries for since and until dates
        self.since_label = tk.Label(self.root, text="Since Date (YYYY-MM-DD):")
        self.since_label.pack(pady=5)
        self.since_entry = tk.Entry(self.root)
        self.since_entry.pack(pady=5)

        self.until_label = tk.Label(self.root, text="Until Date (YYYY-MM-DD):")
        self.until_label.pack(pady=5)
        self.until_entry = tk.Entry(self.root)
        self.until_entry.pack(pady=5)

    def start_trading(self):
        # Start trading logic
        interval = self.interval_var.get()
        messagebox.showinfo("Trading", f"Trading started with interval {interval}!")
        # Here you would start your trading strategy

    def stop_trading(self):
        # Stop trading logic
        messagebox.showinfo("Trading", "Trading stopped!")
        # Here you would stop your trading strategy

    def show_results(self):
        # Show results logic
        messagebox.showinfo("Results", "Showing results!")
        # Example of plotting a chart
        data = pd.DataFrame({
            'Time': pd.date_range(start='1/1/2021', periods=100, freq='D'),
            'Value': np.random.randn(100).cumsum()
        })
        self.plot_results(data)

    def plot_results(self, data):
        fig, ax = plt.subplots()
        ax.plot(data['Time'], data['Value'])
        ax.set(xlabel='Time', ylabel='Value', title='Trading Results')
        ax.grid()

        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    def run_backtest(self):
        interval = self.interval_var.get()
        since = self.since_entry.get() or self.config.SINCE
        until = self.until_entry.get() or self.config.UNTIL
        self.execute_backtest(self.config, interval, since, until)

    def execute_backtest(self, config, interval, since, until):
        db_path = "db/trading_data.db"
        if not os.path.exists("db"):
            os.makedirs("db")

        fetcher = DataFetcher()
        saver = DataSaver(db_path)
        loader = DataLoader(db_path)

        formatted_since = self.format_date(since)
        formatted_until = self.format_date(until)
        table_name = f"{config.BINANCE_SYMBOL.replace('/', '_')}_{interval}_{formatted_since}_{formatted_until}"

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

    def format_date(self, date_str):
        return pd.to_datetime(date_str).strftime('%Y%m%d')


def main():
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

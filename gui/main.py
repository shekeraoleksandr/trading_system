import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkbootstrap import Style
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import pandas as pd
import os
import asyncio
import logging
import backtrader as bt

from backtesting import Backtest
from data import DataFetcher, DataSaver, DataLoader
from analysis import TechnicalIndicators
from telegram_bot import TelegramBot
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='trading_system.log')
logger = logging.getLogger(__name__)


class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Інтелектуальна система автоматизованого трейдингу")
        self.root.geometry("1920x1080")  # Збільшення розміру вікна
        self.root.state('zoomed')  # Встановлення вікна на весь екран
        self.style = Style('darkly')

        self.config = Config()

        self.create_widgets()
        self.configure_grid()

    def create_widgets(self):
        self.wallet_label = ttk.Label(self.root, text="Сума гаманця на початку трейдингу:")
        self.wallet_label.grid(row=0, column=0, padx=10, pady=5, sticky="W")
        self.wallet_entry = ttk.Entry(self.root)
        self.wallet_entry.grid(row=0, column=1, padx=10, pady=5)
        self.wallet_entry.insert(0, str(self.config.INITIAL_CAPITAL))

        self.percent_label = ttk.Label(self.root, text="Відсоток від гаманця на один трейд:")
        self.percent_label.grid(row=1, column=0, padx=10, pady=5, sticky="W")
        self.percent_entry = ttk.Entry(self.root)
        self.percent_entry.grid(row=1, column=1, padx=10, pady=5)
        self.percent_entry.insert(0, str(self.config.TRADE_SIZE))

        self.start_date_label = ttk.Label(self.root, text="Дата початку трейду (YYYY-MM-DD):")
        self.start_date_label.grid(row=2, column=0, padx=10, pady=5, sticky="W")
        self.start_date_entry = ttk.Entry(self.root)
        self.start_date_entry.grid(row=2, column=1, padx=10, pady=5)
        self.start_date_entry.insert(0, self.config.SINCE)

        self.end_date_label = ttk.Label(self.root, text="Дата кінця трейду (YYYY-MM-DD):")
        self.end_date_label.grid(row=3, column=0, padx=10, pady=5, sticky="W")
        self.end_date_entry = ttk.Entry(self.root)
        self.end_date_entry.grid(row=3, column=1, padx=10, pady=5)
        self.end_date_entry.insert(0, self.config.UNTIL)

        self.interval_label = ttk.Label(self.root, text="Інтервал свічок:")
        self.interval_label.grid(row=4, column=0, padx=10, pady=5, sticky="W")
        self.interval_combobox = ttk.Combobox(self.root, values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
        self.interval_combobox.grid(row=4, column=1, padx=10, pady=5)
        self.interval_combobox.set(self.config.TIMEFRAME)

        self.start_button = ttk.Button(self.root, text="Запуск бектестингового трейдингу",
                                       command=self.start_backtesting)
        self.start_button.grid(row=5, column=0, columnspan=2, padx=10, pady=20)

        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.chart = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.canvas.get_tk_widget().grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    def configure_grid(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(6, weight=1)

    def start_backtesting(self):
        try:
            wallet_amount = float(self.wallet_entry.get())
            trade_percent = float(self.percent_entry.get())
            start_date = self.start_date_entry.get() or self.config.SINCE
            end_date = self.end_date_entry.get() or self.config.UNTIL
            interval = self.interval_combobox.get() or self.config.TIMEFRAME

            self.run_backtest(wallet_amount, trade_percent, start_date, end_date, interval)
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            messagebox.showerror("Помилка", "Будь ласка, введіть коректні дані.")

    def run_backtest(self, wallet_amount, trade_percent, start_date, end_date, interval):
        db_path = self.config.DB_PATH
        if not os.path.exists("db"):
            os.makedirs("db")

        fetcher = DataFetcher()
        saver = DataSaver(db_path)
        loader = DataLoader(db_path)

        formatted_since = self.format_date(start_date)
        formatted_until = self.format_date(end_date)
        table_name = f"{self.config.BINANCE_SYMBOL.replace('/', '_')}_{interval}_{formatted_since}_{formatted_until}"

        data = loader.load_data(table_name)
        if data.empty:
            logger.info("No data found in database. Fetching new data...")
            since_timestamp = fetcher.exchange.parse8601(start_date + "T00:00:00Z")
            until_timestamp = fetcher.exchange.parse8601(end_date + "T00:00:00Z")
            data = fetcher.fetch_ohlcv(self.config.BINANCE_SYMBOL, interval, since_timestamp, until_timestamp)
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

        backtest = Backtest(initial_capital=wallet_amount)
        backtest.run(data, trade_percent, self.config.MAX_OPEN_TRADES)
        positions = backtest.get_positions()

        ending_balance = backtest.get_portfolio_value()
        profit_percentage = (ending_balance - wallet_amount) / wallet_amount * 100
        total_trades = backtest.get_total_trades()
        winning_trades = backtest.get_winning_trades()
        losing_trades = backtest.get_losing_trades()

        message = (
            f"Backtest completed successfully.\n\n"
            f"Interval: {interval}\n"
            f"Period: {start_date} to {end_date}\n"
            f"Initial Balance: ${wallet_amount:,.2f}\n"
            f"Ending Balance: ${ending_balance:,.2f}\n"
            f"Profit: {profit_percentage:.2f}%\n"
            f"Total Trades: {total_trades}\n"
            f"Winning Trades: {winning_trades}\n"
            f"Losing Trades: {losing_trades}"
        )

        telegram_bot = TelegramBot(self.config.TELEGRAM_TOKEN, self.config.TELEGRAM_CHAT_ID)
        asyncio.run(telegram_bot.send_message(message))

        logger.info(message)

        self.plot_backtest_results(backtest)

    def plot_backtest_results(self, backtest):
        self.chart.clear()

        # Видалення старого полотна
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()

        fig = backtest.cerebro.plot(iplot=False)[0][0]
        self.figure = fig

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    def format_date(self, date_str):
        return pd.to_datetime(date_str).strftime('%Y%m%d')


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

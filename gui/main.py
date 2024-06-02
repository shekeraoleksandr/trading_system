import threading
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
from signals import SignalGenerator
from telegram_bot import TelegramBot
from config import Config
from trade_simulator import TradeSimulator

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
        self.realtime_trading = False

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self.backtest_frame = ttk.Frame(self.notebook)
        self.realtime_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.backtest_frame, text="Бектест")
        self.notebook.add(self.realtime_frame, text="Торгівля в реальному часі")

        self.create_backtest_widgets()
        self.create_realtime_widgets()
        self.configure_grid()

    def create_backtest_widgets(self):
        self.wallet_label = ttk.Label(self.backtest_frame, text="Сума гаманця на початку трейдингу:")
        self.wallet_label.grid(row=0, column=0, padx=10, pady=5, sticky="W")
        self.wallet_entry = ttk.Entry(self.backtest_frame)
        self.wallet_entry.grid(row=0, column=1, padx=10, pady=5)
        self.wallet_entry.insert(0, str(self.config.INITIAL_CAPITAL))

        self.percent_label = ttk.Label(self.backtest_frame, text="Відсоток від гаманця на один трейд:")
        self.percent_label.grid(row=1, column=0, padx=10, pady=5, sticky="W")
        self.percent_entry = ttk.Entry(self.backtest_frame)
        self.percent_entry.grid(row=1, column=1, padx=10, pady=5)
        self.percent_entry.insert(0, str(self.config.TRADE_SIZE))

        self.start_date_label = ttk.Label(self.backtest_frame, text="Дата початку трейду (YYYY-MM-DD):")
        self.start_date_label.grid(row=2, column=0, padx=10, pady=5, sticky="W")
        self.start_date_entry = ttk.Entry(self.backtest_frame)
        self.start_date_entry.grid(row=2, column=1, padx=10, pady=5)
        self.start_date_entry.insert(0, self.config.SINCE)

        self.end_date_label = ttk.Label(self.backtest_frame, text="Дата кінця трейду (YYYY-MM-DD):")
        self.end_date_label.grid(row=3, column=0, padx=10, pady=5, sticky="W")
        self.end_date_entry = ttk.Entry(self.backtest_frame)
        self.end_date_entry.grid(row=3, column=1, padx=10, pady=5)
        self.end_date_entry.insert(0, self.config.UNTIL)

        self.interval_label = ttk.Label(self.backtest_frame, text="Інтервал свічок:")
        self.interval_label.grid(row=4, column=0, padx=10, pady=5, sticky="W")
        self.interval_combobox = ttk.Combobox(self.backtest_frame, values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
        self.interval_combobox.grid(row=4, column=1, padx=10, pady=5)
        self.interval_combobox.set(self.config.TIMEFRAME)

        self.start_backtest_button = ttk.Button(self.backtest_frame, text="Запуск бектесту", command=self.start_backtesting)
        self.start_backtest_button.grid(row=5, column=0, columnspan=2, padx=10, pady=20)

        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.chart = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.backtest_frame)
        self.canvas.get_tk_widget().grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    def create_realtime_widgets(self):
        self.realtime_wallet_label = ttk.Label(self.realtime_frame, text="Сума гаманця на початку торгівлі:")
        self.realtime_wallet_label.grid(row=0, column=0, padx=10, pady=5, sticky="W")
        self.realtime_wallet_entry = ttk.Entry(self.realtime_frame)
        self.realtime_wallet_entry.grid(row=0, column=1, padx=10, pady=5)
        self.realtime_wallet_entry.insert(0, str(self.config.INITIAL_CAPITAL))

        self.realtime_percent_label = ttk.Label(self.realtime_frame, text="Відсоток від гаманця на один трейд:")
        self.realtime_percent_label.grid(row=1, column=0, padx=10, pady=5, sticky="W")
        self.realtime_percent_entry = ttk.Entry(self.realtime_frame)
        self.realtime_percent_entry.grid(row=1, column=1, padx=10, pady=5)
        self.realtime_percent_entry.insert(0, str(self.config.TRADE_SIZE))

        self.realtime_interval_label = ttk.Label(self.realtime_frame, text="Інтервал свічок:")
        self.realtime_interval_label.grid(row=2, column=0, padx=10, pady=5, sticky="W")
        self.realtime_interval_combobox = ttk.Combobox(self.realtime_frame, values=["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
        self.realtime_interval_combobox.grid(row=2, column=1, padx=10, pady=5)
        self.realtime_interval_combobox.set(self.config.TIMEFRAME)

        self.start_realtime_button = ttk.Button(self.realtime_frame, text="Запуск симуляторної торгівлі", command=self.start_realtime_trading)
        self.start_realtime_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)

        self.stop_realtime_button = ttk.Button(self.realtime_frame, text="Зупинка симуляторної торгівлі", command=self.stop_realtime_trading)
        self.stop_realtime_button.grid(row=4, column=0, columnspan=2, padx=10, pady=20)

    def configure_grid(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.backtest_frame.grid_columnconfigure(0, weight=1)
        self.backtest_frame.grid_columnconfigure(1, weight=1)
        self.backtest_frame.grid_rowconfigure(6, weight=1)

        self.realtime_frame.grid_columnconfigure(0, weight=1)
        self.realtime_frame.grid_columnconfigure(1, weight=1)
        self.realtime_frame.grid_rowconfigure(6, weight=1)

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

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.backtest_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

    def format_date(self, date_str):
        return pd.to_datetime(date_str).strftime('%Y%m%d')

    def start_realtime_trading(self):
        try:
            wallet_amount = float(self.realtime_wallet_entry.get())
            trade_percent = float(self.realtime_percent_entry.get())
            interval = self.realtime_interval_combobox.get() or self.config.TIMEFRAME

            self.realtime_trading = True
            threading.Thread(target=self.run_realtime_trading_thread, args=(wallet_amount, trade_percent, interval)).start()
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            messagebox.showerror("Помилка", "Будь ласка, введіть коректні дані.")

    def stop_realtime_trading(self):
        self.realtime_trading = False
        logger.info("Real-time trading stopped by user.")

    def run_realtime_trading_thread(self, wallet_amount, trade_percent, interval):
        asyncio.run(self.run_realtime_trading(wallet_amount, trade_percent, interval))

    async def run_realtime_trading(self, wallet_amount, trade_percent, interval):
        fetcher = DataFetcher()
        trade_simulator = TradeSimulator(initial_balance=wallet_amount)

        telegram_bot = TelegramBot(self.config.TELEGRAM_TOKEN, self.config.TELEGRAM_CHAT_ID)
        await telegram_bot.send_message(f"Real-time trading started with interval {interval}.")

        sleep_interval = self.get_sleep_interval(interval)

        while self.realtime_trading:
            data = fetcher.fetch_ohlcv(self.config.BINANCE_SYMBOL, interval, fetcher.exchange.milliseconds() - 86400000,
                                       fetcher.exchange.milliseconds())
            if data.empty:
                logger.warning("No data fetched. Waiting for new data...")
                await asyncio.sleep(sleep_interval)
                continue

            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
            data.set_index('timestamp', inplace=True)

            indicators = TechnicalIndicators()
            data = indicators.moving_average(data, period=20)
            data = indicators.rsi(data, period=14)
            data = indicators.macd(data)

            if 'short_mavg' not in data.columns or 'long_mavg' not in data.columns:
                data['short_mavg'] = data['close'].rolling(window=12).mean()
                data['long_mavg'] = data['close'].rolling(window=26).mean()

            signal_generator = SignalGenerator(data, self.config.TELEGRAM_TOKEN, self.config.TELEGRAM_CHAT_ID, trade_simulator,
                                               trade_simulator, trade_percent, self.config.DRY_RUN)
            signal_generator.process_signals()

            # Логування активних ордерів та стану ринку
            active_orders = trade_simulator.get_active_orders()
            market_state = fetcher.fetch_market_state(self.config.BINANCE_SYMBOL)

            logger.info(f"Active orders: {active_orders}")
            logger.info(f"Market state: {market_state}")

            if active_orders:
                for order in active_orders:
                    order_info = f"Order ID: {order['id']}, Status: {order['status']}, Amount: {order['amount']}, Price: {order['price']}"
                    logger.info(order_info)
                    await telegram_bot.send_message(order_info)

            await asyncio.sleep(sleep_interval)

    def get_sleep_interval(self, interval):
        units = {
            'm': 60,
            'h': 3600,
            'd': 86400,
        }
        if interval[-1] in units:
            return int(interval[:-1]) * units[interval[-1]]
        return 60  # default to 60 seconds if interval is not recognized


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()

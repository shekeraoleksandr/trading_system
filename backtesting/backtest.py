import backtrader as bt
from strategies import MovingAverageCrossoverStrategy
import pandas as pd
import matplotlib.pyplot as plt


class Backtest:
    def __init__(self, initial_capital=10000.0):
        self.initial_capital = initial_capital
        self.positions = pd.DataFrame()
        self.cerebro = bt.Cerebro()

    def run(self, data, trade_size, max_open_trades):
        self.cerebro.broker.setcash(self.initial_capital)

        # Додавання даних
        data_feed = bt.feeds.PandasData(dataname=data)
        self.cerebro.adddata(data_feed)

        # Додавання стратегії з параметрами
        self.cerebro.addstrategy(MovingAverageCrossoverStrategy, trade_size=trade_size, max_open_trades=max_open_trades)

        # Запуск бектестингу
        print(f'Starting Portfolio Value: {self.cerebro.broker.getvalue():.2f}')
        strategies = self.cerebro.run()
        ending_value = self.cerebro.broker.getvalue()
        print(f'Ending Portfolio Value: {ending_value:.2f}')

        # Відображення прибутку у відсотках
        profit_percent = ((ending_value - self.initial_capital) / self.initial_capital) * 100
        print(f'Profit Percentage: {profit_percent:.2f}%')

        # Отримання позицій зі стратегії
        self.positions = strategies[0].get_positions()

    def get_positions(self):
        return self.positions

    def get_portfolio_value(self):
        return self.cerebro.broker.getvalue()

    def get_total_trades(self):
        return len(self.positions)

    def get_winning_trades(self):
        if 'profit' in self.positions.columns:
            return len(self.positions[self.positions['profit'] > 0])
        return 0

    def get_losing_trades(self):
        if 'profit' in self.positions.columns:
            return len(self.positions[self.positions['profit'] <= 0])
        return 0

import backtrader as bt
from strategies import MovingAverageCrossoverStrategy


class Backtest:
    def __init__(self, initial_capital=10000.0):
        self.initial_capital = initial_capital

    def run(self, data, trade_size, max_open_trades):
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.initial_capital)

        # Додавання даних
        data_feed = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_feed)

        # Додавання стратегії з параметрами
        cerebro.addstrategy(MovingAverageCrossoverStrategy, trade_size=trade_size, max_open_trades=max_open_trades)

        # Запуск бектестингу
        print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
        cerebro.run()
        ending_value = cerebro.broker.getvalue()
        print(f'Ending Portfolio Value: {ending_value:.2f}')

        # Відображення прибутку у відсотках
        profit_percent = ((ending_value - self.initial_capital) / self.initial_capital) * 100
        print(f'Profit Percentage: {profit_percent:.2f}%')

        cerebro.plot()

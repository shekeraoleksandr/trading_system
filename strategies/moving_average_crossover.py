import backtrader as bt


class MovingAverageCrossoverStrategy(bt.Strategy):
    params = (('short_window', 20), ('long_window', 50), ('trade_size', 0.2), ('max_open_trades', 5),)

    def __init__(self):
        self.short_mavg = bt.ind.SMA(period=self.params.short_window)
        self.long_mavg = bt.ind.SMA(period=self.params.long_window)
        self.crossover = bt.ind.CrossOver(self.short_mavg, self.long_mavg)
        self.order = None  # Трекер для поточної відкритої угоди

    def next(self):
        # Перевірка кількості відкритих угод
        if len(self.broker.positions) >= self.params.max_open_trades:
            return

        if self.order:  # Перевірка наявності активної угоди
            return

        available_cash = self.broker.getcash()
        trade_cash = available_cash * self.params.trade_size  # 20% від доступного капіталу

        if self.crossover > 0:  # Коротка ковзна середня перетинає довгу вгору
            self.order = self.buy(size=trade_cash / self.data.close[0])
            print(f'{self.datas[0].datetime.date(0)}: BUY signal')
        elif self.crossover < 0 and self.position:  # Коротка ковзна середня перетинає довгу вниз
            self.order = self.sell(size=self.position.size)
            print(f'{self.datas[0].datetime.date(0)}: SELL signal')

    def notify_order(self, order):
        if order.status in [order.Completed, order.Canceled, order.Margin]:
            self.order = None  # Скидаємо трекер угоди, коли угода завершена

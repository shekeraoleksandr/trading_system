import matplotlib.pyplot as plt


class Plotter:
    def plot_data(self, data, symbol):
        plt.figure(figsize=(14, 7))

        # Ціна закриття
        plt.subplot(3, 1, 1)
        plt.plot(data['timestamp'], data['close'], label='Close Price')
        plt.plot(data['timestamp'], data['MA_20'], label='MA 20')
        plt.title(f'{symbol} Price and Moving Average')
        plt.legend()

        # RSI
        plt.subplot(3, 1, 2)
        plt.plot(data['timestamp'], data['RSI_14'], label='RSI 14', color='orange')
        plt.axhline(30, color='red', linestyle='--')
        plt.axhline(70, color='green', linestyle='--')
        plt.title(f'{symbol} RSI')
        plt.legend()

        # MACD
        plt.subplot(3, 1, 3)
        plt.plot(data['timestamp'], data['MACD'], label='MACD', color='purple')
        plt.plot(data['timestamp'], data['Signal_Line'], label='Signal Line', color='red')
        plt.title(f'{symbol} MACD')
        plt.legend()

        plt.tight_layout()
        plt.show()

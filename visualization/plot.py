import matplotlib.pyplot as plt


class Plotter:
    @staticmethod
    def plot_data(data, symbol):
        plt.figure(figsize=(14, 7))
        plt.plot(data.index, data['close'], label='Close Price')  # Використання індексу для побудови графіка
        plt.title(f'{symbol} Close Price')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid()
        plt.savefig('plots/price_plot.png')  # Збереження графіка в файл
        plt.close()

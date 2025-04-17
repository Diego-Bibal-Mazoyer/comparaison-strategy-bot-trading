import backtrader as bt

class BuyHoldStrategy(bt.Strategy):
    """
    Stratégie Buy & Hold : achète tout et conserve jusqu'à la fin du backtest.
    """
    def __init__(self):
        self.bought = False

    def next(self):
        # À la première bougie, on achète tout le capital disponible
        if not self.position and not self.bought:
            size = self.broker.getcash() / self.data.close[0]
            self.buy(size=size)
            self.bought = True


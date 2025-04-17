import backtrader as bt

class MomentumStrategy(bt.Strategy):
    params = (
        ('ema_fast', 20),
        ('ema_slow', 50),
        ('rsi_period', 14),
        ('rsi_buy', 55),
        ('rsi_sell', 45),
        ('atr_period', 14),
        ('risk_per_trade', 0.01),
    )

    def __init__(self):
        # EMA rapides et lentes
        self.ema_fast = bt.ind.EMA(self.data.close, period=self.p.ema_fast)
        self.ema_slow = bt.ind.EMA(self.data.close, period=self.p.ema_slow)
        # CrossOver (>0 quand ema_fast croise au-dessus de ema_slow)
        self.crossover = bt.ind.CrossOver(self.ema_fast, self.ema_slow)
        # RSI & ATR
        self.rsi = bt.ind.RSI(self.data.close, period=self.p.rsi_period)
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        # Pour suivre l’ordre en cours et le prix de stop
        self.order = None
        self.stop_price = None

    def next(self):
        # si un ordre est en cours, on ne fait rien
        if self.order:
            return

        cash = self.broker.getcash()
        size = (cash * self.p.risk_per_trade) / self.atr[0]

        # --- Pas de position : on achète sur croisement haussier + RSI > seuil
        if not self.position:
            if self.crossover > 0 and self.rsi[0] > self.p.rsi_buy:
                self.order = self.buy(size=size)
                # stop-loss dynamique 1×ATR sous le prix d'entrée
                self.stop_price = self.data.close[0] - self.atr[0]

        # --- Si position ouverte : conditions de sortie
        else:
            # stop-loss atteint
            if self.data.close[0] < self.stop_price:
                self.order = self.close()
            # croisement baissier ou RSI faible
            elif self.crossover < 0 or self.rsi[0] < self.p.rsi_sell:
                self.order = self.close()


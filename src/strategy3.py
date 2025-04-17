import backtrader as bt

class EnhancedBreakoutStrategy(bt.Strategy):
    """
    Stratégie de breakout enrichie pour retail :
    • Filtre de tendance (ADX > 25)
    • Filtre volume (> 1.5× moyenne 20j)
    • Breakout sur bandes ATR (SMA20 ± 1.5 ATR)
    • Partial scaling : 50% à +1×ATR, reste à +2×ATR
    • Stop-loss 1×ATR sous l’entrée ou trailing stop
    • Time-stop après 20 jours
    """
    params = dict(
        sma_period     = 20,
        atr_period     = 14,
        adx_period     = 14,
        vol_period     = 20,
        vol_multiplier = 1.5,
        trend_adx      = 25,
        tp1_atr        = 1.0,
        tp2_atr        = 2.0,
        risk_per_trade = 0.01,
        max_hold_days  = 20,
    )

    def __init__(self):
        # Moyenne mobile
        self.sma = bt.ind.SMA(self.data.close, period=self.p.sma_period)
        # ATR
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        # ADX pour tendance
        self.adx = bt.ind.AverageDirectionalMovementIndex(self.data, period=self.p.adx_period)
        # Volume moyen
        self.vol_ma = bt.ind.SMA(self.data.volume, period=self.p.vol_period)
        # Bandes ATR
        self.upper = self.sma + self.p.tp2_atr * self.atr
        self.lower = self.sma - self.p.tp2_atr * self.atr

        self.order = None
        self.entry_price = None
        self.stop_price  = None
        self.bar_exec    = 0
        self.scaled      = False

    def next(self):
        # Attendre assez de données
        if len(self) < max(self.p.sma_period, self.p.atr_period, self.p.adx_period, self.p.vol_period):
            return

        # Si ordre en attente, ne rien faire
        if self.order:
            return

        cash = self.broker.getcash()
        size = (cash * self.p.risk_per_trade) / self.atr[0]

        # Conditions d'entrée
        if not self.position:
            cond_trend = self.adx[0] > self.p.trend_adx
            cond_vol   = self.data.volume[0] > self.p.vol_multiplier * self.vol_ma[0]
            cond_price = self.data.close[0] > self.upper[0]
            if cond_trend and cond_vol and cond_price:
                # Entrée full position
                self.order = self.buy(size=size)
                self.entry_price = self.data.close[0]
                self.stop_price  = self.entry_price - self.atr[0]
                self.bar_exec    = len(self)
                self.scaled      = False
        else:
            days_held = len(self) - self.bar_exec
            price     = self.data.close[0]

            # 1) Partial scaling à +1×ATR
            if not self.scaled and price >= self.entry_price + self.p.tp1_atr * self.atr[0]:
                # Fermer 50% de la position
                self.close(size=self.position.size * 0.5)
                self.scaled = True

            # 2) Sortie totale à +2×ATR
            elif price >= self.entry_price + self.p.tp2_atr * self.atr[0]:
                self.order = self.close()

            # 3) Trailing stop sur plus haut depuis entrée moins 1×ATR
            else:
                high_since = max(self.data.high.get(size=days_held+1))
                trail_stop = high_since - self.atr[0]
                if price < trail_stop:
                    self.order = self.close()

            # 4) Stop-loss initial
            if self.order is None and price < self.stop_price:
                self.order = self.close()

            # 5) Time-stop
            if self.order is None and days_held >= self.p.max_hold_days:
                self.order = self.close()


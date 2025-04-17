import backtrader as bt

class DonchianBreakoutStrategy(bt.Strategy):
    """
    Stratégie de breakout Donchian corrigée :
    • Achat si close > max(high[-N:-1])  (canal sur N jours précédents)
    • Vente si close < min(low[-N:-1])
    • Stop‑loss 1×ATR sous l’entrée
    • Time‑stop après M jours
    """
    params = dict(
        donchian_period = 20,
        atr_period      = 14,
        risk_per_trade  = 0.01,
        max_hold_days   = 20,
    )

    def __init__(self):
        # Canal Donchian des N jours **précédents** (shift de 1)
        self.dc_up   = bt.indicators.Highest(
            self.data.high(-1),
            period=self.p.donchian_period,
            subplot=False
        )
        self.dc_down = bt.indicators.Lowest(
            self.data.low(-1),
            period=self.p.donchian_period,
            subplot=False
        )
        # ATR pour stop‑loss
        self.atr     = bt.indicators.ATR(
            self.data,
            period=self.p.atr_period
        )
        self.order      = None
        self.stop_price = None
        self.bar_exec   = 0

    def next(self):
        # Ne pas agir tant qu'on n'a pas N+1 bougies
        if len(self) <= self.p.donchian_period:
            return

        # Si un ordre est en cours → attente
        if self.order:
            return

        cash = self.broker.getcash()
        size = (cash * self.p.risk_per_trade) / self.atr[0]

        # --- Entrée : breakout haussier sur les N derniers jours (hors jour courant)
        if not self.position and self.data.close[0] > self.dc_up[0]:
            self.order = self.buy(size=size)
            self.bar_exec   = len(self)
            self.stop_price = self.data.close[0] - self.atr[0]

        # --- Sorties
        elif self.position:
            days_held = len(self) - self.bar_exec

            # 1) breakout baissier
            if self.data.close[0] < self.dc_down[0]:
                self.order = self.close()

            # 2) stop‑loss
            elif self.data.close[0] < self.stop_price:
                self.order = self.close()

            # 3) time‑stop
            elif days_held >= self.p.max_hold_days:
                self.order = self.close()


import backtrader as bt

class RegimeAwareBreakoutStrategy(bt.Strategy):
    """
    • Trade only if price > SMA200 (bull); liquidate if price < SMA200 (bear).
    • Entry on breakout above SMA20 + 1×ATR.
    • Stop-loss 1×ATR below entry; trailing stop at 1×ATR off highest high.
    • Position size = 2% in bull, else 0%.
    """
    params = dict(
        sma_long       = 200,
        sma_short      = 20,
        atr_period     = 14,
        risk_bull      = 0.02,
        risk_bear      = 0.0,
        max_hold_days  = 20,
    )

    def __init__(self):
        # Long‐term trend filter
        self.sma_long   = bt.ind.SMA(self.data.close, period=self.p.sma_long)
        # ATR breakout channel
        self.sma_short  = bt.ind.SMA(self.data.close, period=self.p.sma_short)
        self.atr        = bt.ind.ATR(self.data, period=self.p.atr_period)
        self.upper      = self.sma_short + self.atr
        # State
        self.order      = None
        self.entry_price= None
        self.stop_price = None
        self.bar_exec   = 0
        self.peak_price = None

    def next(self):
        price = self.data.close[0]

        # Bear market: exit everything immediately
        if price < self.sma_long[0]:
            if self.position:
                self.close()
            return

        # No new trades if already an order pending
        if self.order:
            return

        cash = self.broker.getcash()
        # Dynamic sizing: 2% in bull, else 0
        risk_pct = self.p.risk_bull
        size = (cash * risk_pct) / self.atr[0] if self.atr[0] > 0 else 0

        # --- Entry: breakout above short‑term channel
        if not self.position and price > self.upper[0] and size>0:
            self.order       = self.buy(size=size)
            self.entry_price = price
            self.stop_price  = price - self.atr[0]
            self.bar_exec    = len(self)
            self.peak_price  = price

        # --- Exit logic
        elif self.position:
            days_held = len(self) - self.bar_exec
            # Update peak
            self.peak_price = max(self.peak_price, price)

            # 1) Trailing stop at 1×ATR off highest high
            if price < (self.peak_price - self.atr[0]):
                self.order = self.close()

            # 2) Initial stop‑loss
            elif price < self.stop_price:
                self.order = self.close()

            # 3) Time‑stop
            elif days_held >= self.p.max_hold_days:
                self.order = self.close()


import backtrader as bt

class DynamicSafeRebalance(bt.Strategy):
    """
    Portefeuille momentum hebdo enrichi :
    • Actifs risqués + actif refuge (paramétrable)
    • Allocation dynamique : poids ∝ rendement / volatilité sur lookback
    • Rebalance tous les rebalance_period jours
    • Stop‑loss global : si drawdown > threshold, 100% en actif refuge
    """
    params = dict(
        lookback_days     = 5,
        rebalance_period  = 5,
        vol_lookback      = 20,
        stoploss_pct      = 0.05,  # 5% drawdown
        safe_asset        = 'GLD', # nom de l'actif refuge
    )

    def __init__(self):
        self.last_bar   = None
        self.peak_value = None

        # Indicateur de volatilité sur vols lookback
        self.stddev = bt.ind.StdDev(self.data.close, period=self.p.vol_lookback)

        # Identification des feeds risqués et du refuge
        self.risky_data = []
        self.refuge_data = None
        for d in self.datas:
            # backtrader datafeed a attribut _name
            name = getattr(d, '_name', None)
            if name == self.p.safe_asset:
                self.refuge_data = d
            else:
                self.risky_data.append(d)
        # Si l'actif refuge introuvable, on prend le dernier feed
        if self.refuge_data is None and self.datas:
            self.refuge_data = self.datas[-1]

    def next(self):
        # Update peak value
        value = self.broker.getvalue()
        if self.peak_value is None or value > self.peak_value:
            self.peak_value = value

        # Global stop-loss drawdown
        if self.peak_value and (self.peak_value - value) / self.peak_value > self.p.stoploss_pct:
            # Passer 100% en refuge
            for d in self.risky_data:
                self.order_target_percent(d, target=0.0)
            self.order_target_percent(self.refuge_data, target=1.0)
            return

        # Attendre assez de données
        if len(self) <= max(self.p.lookback_days, self.p.vol_lookback, 1):
            return

        # Vérifier périodicité de rebalance
        do_reb = self.last_bar is None or (len(self) >= self.last_bar + self.p.rebalance_period)
        if not do_reb:
            return

        # Calcul rendements et volatilité
        returns = []
        vols    = []
        for d in self.risky_data:
            past = d.close[-self.p.lookback_days]
            now  = d.close[0]
            r = max((now / past) - 1.0, 0.0)
            returns.append(r)

            v = self.stddev[0]
            vols.append(v if v > 0 else 1e-6)

        # Poids dynamiques
        weighted = [r/v for r, v in zip(returns, vols)]
        total_w  = sum(weighted)

        if total_w <= 0:
            # tout en refuge
            for d in self.risky_data:
                self.order_target_percent(d, target=0.0)
            self.order_target_percent(self.refuge_data, target=1.0)
        else:
            # appliquer poids aux risqués
            for d, w in zip(self.risky_data, weighted):
                self.order_target_percent(d, target=(w/total_w))
            # et rester 0% refuge
            self.order_target_percent(self.refuge_data, target=0.0)

        self.last_bar = len(self)


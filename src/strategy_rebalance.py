import backtrader as bt

class WeeklyMomentumRebalance(bt.Strategy):
    """
    Portefeuille momentum rééquilibré tous les rebalance_period jours :
    • lookback_days : fenêtre de calcul du rendement (ex. 5 jours)
    • rebalance_period : fréquence en jours de bourse (ex. 5 jour = hebdo)
    """
    params = dict(
        lookback_days     = 5,   # fenêtre pour calculer le rendement
        rebalance_period  = 5,   # tous les 5 jours de bourse
    )

    def __init__(self):
        self.last_bar = None  # index du dernier rebalance

    def next(self):
        # On attend d'avoir assez de données pour lookback et éviter 1er passage
        if len(self) <= max(self.p.lookback_days, 1):
            return

        # Si jamais rebalance, on rebalance sur la 1ère bougie utile
        if self.last_bar is None:
            do_reb = True
        else:
            # Rebalance si on est à >= last_bar + rebalance_period
            do_reb = len(self) >= self.last_bar + self.p.rebalance_period

        if not do_reb:
            return

        # Calcul des rendements sur lookback_days
        rets = []
        for d in self.datas:
            past = d.close[-self.p.lookback_days]
            now  = d.close[0]
            rets.append(max((now / past) - 1.0, 0.0))

        total_pos = sum(rets)
        # Si aucun rendement positif, mettre tout en cash
        if total_pos == 0:
            for d in self.datas:
                self.order_target_percent(d, target=0.0)
            self.last_bar = len(self)
            return

        # Sinon, rééquilibrer selon les poids ∝ rendement
        for d, r in zip(self.datas, rets):
            self.order_target_percent(d, target=(r/total_pos))

        # Mémoriser le bar de rebalance
        self.last_bar = len(self)


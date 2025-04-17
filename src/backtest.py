import backtrader as bt
import pandas as pd
from data_loader import download_data
from strategy import MomentumStrategy

if __name__ == "__main__":
    # 1. Initialisation de Cerebro
    cerebro = bt.Cerebro()

    # 2. Téléchargement des données (par défaut SPY, modifiez si besoin)
    df = download_data("SPY", period="2y", interval="1d")

    # 3. Aplatir les colonnes si MultiIndex (niveau 0 = attributs)
    if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)

    # 4. Création du feed Backtrader
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # 5. Ajout de la stratégie
    cerebro.addstrategy(MomentumStrategy)

    # 6. Initialisation du capital
    cerebro.broker.setcash(100000)

    # 7. Ajout d'analyzers pour les métriques
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown,    _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # 8. Exécution du backtest
    strat = cerebro.run()[0]

    # 9. Récupération des résultats
    sharpe = strat.analyzers.sharpe.get_analysis().get('sharperatio', None)
    dd     = strat.analyzers.drawdown.get_analysis()['max']['drawdown']
    trades_analysis = strat.analyzers.trades.get_analysis()

    # Debug : affichage complet pour vérifier la structure
    print("TradeAnalyzer full output:", trades_analysis)

    # Nombre total de trades fermés
    total_trades = trades_analysis.get('total', {}).get('total', 0)

    # 10. Affichage final
    print(f"Sharpe Ratio  : {sharpe}")
    print(f"Max Drawdown  : {dd}%")
    print(f"Total Trades   : {total_trades}")


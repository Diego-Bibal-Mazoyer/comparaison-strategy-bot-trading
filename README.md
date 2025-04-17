Comparaison Strategy Bot Trading

Un projet Python sous Ubuntu (WSL ou natif) pour backtester et comparer plusieurs stratégies de trading « swing » sur un univers d’actifs diversifié, avec interface Streamlit.

---

Structure du dépôt:

comparaison-strategy-bot-trading/
├── streamlit_app.py        # Interface principale
├── src/
│   ├── data_loader.py      # Téléchargement yfinance
│   ├── indicators.py       # EMA, RSI, ATR
│   ├── strategy.py         # MomentumStrategy (EMA20/50 + RSI + ATR)
│   ├── strategy2.py        # DonchianBreakoutStrategy
│   ├── strategy3.py        # EnhancedBreakoutStrategy (ADX, volume, ATR bands…)
│   ├── strategy4.py        # RegimeAwareBreakoutStrategy (SMA200 bull/bear)
│   ├── strategy_rebalance.py  # WeeklyMomentumRebalance
│   ├── strategy5.py        # DynamicSafeRebalance (momentum/vol + refuge + stop-loss portfolio)
├── data/                   # (optionnel) cache des CSV yfinance
├── venv/                   # environnement virtuel
├── .gitignore
└── README.txt              # ce fichier

---

Installation:

1. Cloner le dépôt et se placer dans le dossier :
   git clone git@github.com:ton-user/comparaison-strategy-bot-trading.git
   cd comparaison-strategy-bot-trading

2. Créer et activer un environnement virtuel :
   python3 -m venv venv
   source venv/bin/activate

3. Installer les dépendances :
   pip install -r requirements.txt
   (Backtrader, yfinance, streamlit, pandas, altair…)

---

Lancer l’interface:

streamlit run streamlit_app.py

Sidebar:

- Choix de la stratégie : Momentum, Donchian Breakout, Enhanced Breakout, Regime‑Aware Breakout, Weekly Rebalance, Dynamic Safe Rebalance
- Sélection des actifs (ETF, Actions, Crypto)
- Période historique (6mo, 1y, 2y)
- Pour les rebalances : Fenêtre rendement, Fréquence rebalance, Fenêtre vol, Stop-loss drawdown %

---

Affichages:

- Performance cumulative par actif (stratégie choisie)
- Buy & Hold par actif
- Performance cumulative du portefeuille (stratégie vs buy & hold)
- Métriques agrégées : Total Return, CAGR, Volatilité ann., Sharpe Ratio, Max Drawdown

---

Fonctionnement des stratégies:

- MomentumStrategy : EMA20/50 + RSI + ATR
- DonchianBreakoutStrategy : breakout Donchian 20j
- EnhancedBreakoutStrategy : ADX, volume, bandes ATR, scaling, trailing stop
- RegimeAwareBreakoutStrategy : breakout ATR short-term, bull/bear SMA200
- WeeklyMomentumRebalance : rebalancement selon rendement hebdo
- DynamicSafeRebalance : poids dynamiques rendement/volatilité, refuge GLD en cas de drawdown

---

Conseils d’optimisation:

- Grid search sur lookback_days, rebalance_period, vol_lookback, stoploss_pct
- Walk‑forward in‑sample vs out‑of‑sample
- Ajout d’un actif refuge (GLD, USD, obligations) pour protéger en bear market

---

Auteur : Diego Bibal Mazoyer

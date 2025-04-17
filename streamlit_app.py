import streamlit as st
import backtrader as bt
import pandas as pd
import sys
# Pour importer vos modules depuis src/
sys.path.append("src")

from data_loader                  import download_data
from indicators                   import EMA, RSI, ATR
from strategy                     import MomentumStrategy
from strategy2                    import DonchianBreakoutStrategy
from strategy3                    import EnhancedBreakoutStrategy
from strategy4                    import RegimeAwareBreakoutStrategy
from strategy_rebalance           import WeeklyMomentumRebalance
from strategy5                    import DynamicSafeRebalance

import altair as alt

# --- Constantes ---
INITIAL_CAPITAL = 100000
TRADING_DAYS    = 252

# Mapping des stratégies
STRAT_MAP = {
    "Momentum":              MomentumStrategy,
    "Donchian Breakout":     DonchianBreakoutStrategy,
    "Enhanced Breakout":     EnhancedBreakoutStrategy,
    "Regime‑Aware Breakout": RegimeAwareBreakoutStrategy,
    "Weekly Rebalance":      WeeklyMomentumRebalance,
    "Dynamic Safe Rebalance": DynamicSafeRebalance
}

# Sélecteur de stratégie
strategy_name = st.sidebar.selectbox(
    "Choisissez la stratégie",
    options=list(STRAT_MAP.keys())
)
StratCls = STRAT_MAP[strategy_name]

# Univers d'actifs
CATEGORIES = {
    "ETF":     ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF"],
    "Actions": ["AAPL","MSFT","TSLA","NVDA","AMZN","GOOGL"],
    "Crypto":  ["BTC-USD","ETH-USD","BNB-USD","ADA-USD","SOL-USD"]
}

st.title(f"Swing Bot 📈 : {strategy_name}")

# Sélection des actifs
selected_tickers = []
for cat, assets in CATEGORIES.items():
    chosen = st.sidebar.multiselect(
        f"Sélectionner {cat}",
        options=assets,
        default=assets
    )
    selected_tickers.extend(chosen)

# Période historique
duration = st.sidebar.selectbox(
    "Période historique",
    ["6mo","1y","2y"],
    index=2
)

# Si on utilise la stratégie dynamique with safe asset, on force GLD en refuge
if strategy_name == "Dynamic Safe Rebalance":
    if "GLD" not in selected_tickers:
        selected_tickers.append("GLD")

# Paramètres spécifiques aux rebalances
if strategy_name in ["Weekly Rebalance", "Dynamic Safe Rebalance"]:
    lookback_days    = st.sidebar.slider("Fenêtre rendement (jours)", 1, 63, 5, 1)
    rebalance_period = st.sidebar.slider("Fréquence rebalance (jours)", 1, 63, 5, 1)
    if strategy_name == "Dynamic Safe Rebalance":
        vol_lookback = st.sidebar.slider("Fenêtre vol (jours)", 5, 63, 20, 1)
        stoploss_pct = st.sidebar.slider("Stop‑loss drawdown (%)", 1, 20, 5, 1) / 100
    else:
        vol_lookback = None
        stoploss_pct = None
else:
    lookback_days = rebalance_period = vol_lookback = stoploss_pct = None

if not selected_tickers:
    st.sidebar.error("Veuillez sélectionner au moins un actif.")
    st.stop()

# --- Helpers ---

@st.cache_data
def load_and_prep(ticker, period):
    df = download_data(ticker, period=period, interval="1d")
    if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    df.index = pd.to_datetime(df.index)
    return df

def plot_interactive(df, title, y_label="Equity"):
    df0      = df.reset_index()
    date_col = df0.columns[0]
    dfm      = df0.melt(id_vars=date_col, var_name="Series", value_name=y_label)
    chart = (
        alt.Chart(dfm)
        .mark_line()
        .encode(
            x=alt.X(f"{date_col}:T", title="Date"),
            y=alt.Y(f"{y_label}:Q", title=y_label),
            color="Series:N",
        )
        .properties(title=title, width=700, height=400)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

def backtest_returns(df, StratClass):
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(bt.feeds.PandasData(dataname=df))
    cerebro.addstrategy(StratClass)
    cerebro.broker.setcash(1.0)
    cerebro.addanalyzer(
        bt.analyzers.TimeReturn,
        timeframe=bt.TimeFrame.Days,
        _name="timereturn"
    )
    result = cerebro.run()[0]
    ret = result.analyzers.timereturn.get_analysis()
    return pd.Series(ret).sort_index().astype(float)

def backtest_portfolio(strategy_cls, tickers, duration):
    cerebro = bt.Cerebro(stdstats=False)
    # For rebalance strategies ensure SPY first, GLD last
    if strategy_cls in [WeeklyMomentumRebalance, DynamicSafeRebalance]:
        # place SPY first if present
        if "SPY" in tickers:
            tickers = ["SPY"] + [t for t in tickers if t != "SPY"]
        # ensure GLD is last
        if "GLD" in tickers:
            tickers = [t for t in tickers if t != "GLD"] + ["GLD"]
    for tic in tickers:
        df = load_and_prep(tic, duration)
        data = bt.feeds.PandasData(dataname=df, name=tic)
        cerebro.adddata(data)
    # pass dynamic params
    if strategy_cls is WeeklyMomentumRebalance:
        cerebro.addstrategy(
            strategy_cls,
            lookback_days=lookback_days,
            rebalance_period=rebalance_period
        )
    elif strategy_cls is DynamicSafeRebalance:
        cerebro.addstrategy(
            strategy_cls,
            lookback_days=lookback_days,
            rebalance_period=rebalance_period,
            vol_lookback=vol_lookback,
            stoploss_pct=stoploss_pct,
            safe_asset="GLD"
        )
    else:
        cerebro.addstrategy(strategy_cls)
    cerebro.broker.setcash(INITIAL_CAPITAL)
    cerebro.addanalyzer(
        bt.analyzers.TimeReturn,
        timeframe=bt.TimeFrame.Days,
        _name="timereturn"
    )
    strat = cerebro.run()[0]
    ret = strat.analyzers.timereturn.get_analysis()
    series = pd.Series(ret).sort_index().astype(float)
    return (1 + series).cumprod() * INITIAL_CAPITAL

# --- Logique principale ---

if strategy_name in ["Weekly Rebalance", "Dynamic Safe Rebalance"]:
    eq_port = backtest_portfolio(StratCls, selected_tickers, duration)

    # Build Buy & Hold curves for comparison
    bh_curves = {}
    for tic in selected_tickers:
        df_t = load_and_prep(tic, duration)
        bh = (df_t["Close"] / df_t["Close"].iloc[0]) * (INITIAL_CAPITAL / len(selected_tickers))
        bh.index = pd.to_datetime(bh.index)
        bh_curves[tic] = bh
    df_bh = pd.DataFrame(bh_curves)
    idx   = eq_port.index.union(df_bh.index).sort_values()
    df_bh = df_bh.reindex(idx).ffill()
    bh_port = df_bh.sum(axis=1)

    if eq_port.empty:
        st.warning("Pas assez de données pour le rebalancement.")
    else:
        st.subheader("Buy & Hold par actif")
        plot_interactive(df_bh, "Buy & Hold par actif")

        st.subheader("Performance cumulative du portefeuille")
        port_df = pd.DataFrame({
            f"{strategy_name} Portfolio": eq_port,
            "Buy & Hold Portfolio":       bh_port
        })
        plot_interactive(port_df, "Portefeuille : Rebalance vs Buy & Hold", y_label="Valorisation")

        # Métriques agrégées
        first, last = eq_port.iloc[0], eq_port.iloc[-1]
        total_ret = (last / first - 1) * 100
        cagr      = (last / first) ** (TRADING_DAYS / len(eq_port)) - 1
        rets      = eq_port.pct_change().dropna()
        vol       = rets.std() * (TRADING_DAYS**0.5) * 100
        sharpe    = rets.mean() / rets.std() * (TRADING_DAYS**0.5)
        max_dd    = ((eq_port.cummax() - eq_port) / eq_port.cummax()).max() * 100

        st.subheader("Métriques agrégées")
        st.write(f"**Total Return**: {total_ret:.2f}%")
        st.write(f"**CAGR**: {cagr*100:.2f}%")
        st.write(f"**Volatilité ann.**: {vol:.2f}%")
        st.write(f"**Sharpe Ratio**: {sharpe:.2f}")
        st.write(f"**Max Drawdown**: {max_dd:.2f}%")

else:
    # Backtest et Buy & Hold par actif
    strat_curves, bh_curves = {}, {}
    for tic in selected_tickers:
        df_t = load_and_prep(tic, duration)

        sr = backtest_returns(df_t, StratCls)
        eq = (1 + sr).cumprod() * (INITIAL_CAPITAL / len(selected_tickers))
        eq.index = pd.to_datetime(eq.index)
        strat_curves[tic] = eq

        bh = (df_t["Close"] / df_t["Close"].iloc[0]) * (INITIAL_CAPITAL / len(selected_tickers))
        bh.index = pd.to_datetime(bh.index)
        bh_curves[tic] = bh

    df_strat = pd.DataFrame(strat_curves)
    df_bh    = pd.DataFrame(bh_curves)
    idx      = df_strat.index.union(df_bh.index).sort_values()
    df_strat = df_strat.reindex(idx).ffill()
    df_bh    = df_bh.reindex(idx).ffill()

    eq_port = df_strat.sum(axis=1)
    bh_port = df_bh.sum(axis=1)

    st.subheader(f"Performance cumulative par actif ({strategy_name})")
    plot_interactive(df_strat, f"{strategy_name} par actif")

    st.subheader("Buy & Hold par actif")
    plot_interactive(df_bh, "Buy & Hold par actif")

    st.subheader("Performance cumulative du portefeuille")
    port_df = pd.DataFrame({
        f"{strategy_name} Portfolio": eq_port,
        "Buy & Hold Portfolio":      bh_port
    })
    plot_interactive(port_df, "Portefeuille : Stratégie vs Buy & Hold", y_label="Valorisation")

    st.subheader("Métriques agrégées du portefeuille")
    rets   = eq_port.pct_change().dropna()
    sharpe = rets.mean() / rets.std() * (TRADING_DAYS**0.5)
    vol    = rets.std() * (TRADING_DAYS**0.5) * 100
    total_ret = (eq_port.iloc[-1] / eq_port.iloc[0] - 1) * 100
    cagr      = (eq_port.iloc[-1] / eq_port.iloc[0]) ** (TRADING_DAYS / len(eq_port)) - 1
    max_dd    = ((eq_port.cummax() - eq_port) / eq_port.cummax()).max() * 100

    st.write(f"**Total Return**: {total_ret:.2f}%")
    st.write(f"**CAGR**: {cagr*100:.2f}%")
    st.write(f"**Volatilité ann.**: {vol:.2f}%")
    st.write(f"**Sharpe Ratio**: {sharpe:.2f}")
    st.write(f"**Max Drawdown**: {max_dd:.2f}%")

# Footer
st.markdown("---")
st.write("Développé avec Streamlit, Backtrader et Altair.")


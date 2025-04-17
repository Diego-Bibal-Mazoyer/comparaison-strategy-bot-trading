# src/debug_signals.py

from data_loader import download_data
from indicators  import EMA, RSI, ATR
import pandas as pd

def main():
    # 1. Récupération des données
    df = download_data("SPY", period="2y", interval="1d")

    # 2. Aplatir les colonnes MultiIndex si nécessaire (on garde le level 0)
    if hasattr(df.columns, 'nlevels') and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)

    # 3. Calcul des indicateurs
    df['EMA20'] = EMA(df, 20)
    df['EMA50'] = EMA(df, 50)
    df['RSI14'] = RSI(df, 14)

    # 4. Génération des signaux
    df['signal_ema'] = df['EMA20'] > df['EMA50']
    # Pour ignorer temporairement le RSI, on met RSI>0
    df['signal_rsi'] = df['RSI14'] > 0
    df['signal']     = df['signal_ema'] & df['signal_rsi']

    # 5. Affichage des résultats
    print(f"Colonnes après aplatissement : {list(df.columns)}\n")
    print(f"Jours EMA20>EMA50 : {df['signal_ema'].sum()}")
    print(f"Jours validés par signal complet : {df['signal'].sum()}\n")
    print("Exemples de jours avec signal :")
    print(df.loc[df['signal'], ['Close','EMA20','EMA50','RSI14']].head())

if __name__ == "__main__":
    main()


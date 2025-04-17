import yfinance as yf
import pandas as pd
import os

def download_data(ticker: str, period: str = '2y', interval: str = '1d') -> pd.DataFrame:
    """
    Télécharge les données OHLCV pour un ticker donné via yfinance,
    les nettoie et les enregistre dans data/raw/.
    """
    # 1. Récupération
    df = yf.download(ticker, period=period, interval=interval)
    if df.empty:
        raise ValueError(f"Aucune donnée pour le ticker {ticker} (période={period}, interval={interval})")

    # 2. Nettoyage
    df.dropna(inplace=True)

    # 3. Création du dossier s'il n'existe pas
    os.makedirs(os.path.join('..', 'data', 'raw'), exist_ok=True)

    # 4. Sauvegarde CSV
    out_path = os.path.join('..', 'data', 'raw', f'{ticker}.csv')
    df.to_csv(out_path)
    print(f"Données enregistrées dans {out_path}")

    return df

# Test rapide si ce fichier est exécuté directement
if __name__ == "__main__":
    # Exemple : télécharger 1 an de données journalières pour SPY
    df = download_data("SPY", period="1y", interval="1d")
    print(df.head())


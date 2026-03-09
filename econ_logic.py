import pandas as pd
import yfinance as yf

def get_market_correlation(ticker_symbol):
    """Pulls live market volatility data."""
    try:
        data = yf.download(ticker_symbol, start="2024-01-01")['Close']
        returns = data.pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5) 
        return round(volatility, 4)
    except:
        return 0.0

def apply_inflation_adjustment(amount, rate=0.035):
    """Adjusts nominal spending for 2024-2026 inflation."""
    return round(amount / (1 + rate), 2)
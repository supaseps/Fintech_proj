"""
Backend logic for the stock analysis app.

These functions are pure data functions - they fetch data and return
DataFrames/values. They do NOT call input() or plt.show(), so they can be
safely imported and used by a frontend (Streamlit, Flask, CLI, etc.).
"""

import yfinance as yf


def get_moving_averages(stock):
    """
    Fetches 5y of price history and computes SMA50/SMA200.

    Returns a tuple: (data, signal)
        data   -> DataFrame with Close, SMA50, SMA200 columns (None if not found)
        signal -> str describing bullish/bearish/equal/insufficient data (None if not found)
    """
    data = yf.download(stock, period="5y")

    if data.empty:
        return None, "No stock found"

    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()

    sma50_clean = data['SMA50'].dropna()
    sma200_clean = data['SMA200'].dropna()

    if sma50_clean.empty or sma200_clean.empty:
        signal = "Not enough history to compute a signal yet"
    else:
        latest_sma50 = sma50_clean.iloc[-1]
        latest_sma200 = sma200_clean.iloc[-1]

        if latest_sma50 > latest_sma200:
            signal = "Short term bullish (SMA50 > SMA200)"
        elif latest_sma200 > latest_sma50:
            signal = "Short term bearish (SMA200 > SMA50)"
        else:
            signal = "Equal"

    return data, signal


def get_rsi(stock, period="2y", window=14):
    """
    Fetches price history and computes the Relative Strength Index (RSI).

    Returns a DataFrame with Close, Gains, Losses, RSI columns
    (None if the stock was not found).
    """
    data = yf.download(stock, period=period, interval="1d")

    if data.empty:
        return None

    data["Gains"] = data["Close"].diff().fillna(0).clip(lower=0)
    data["Losses"] = data["Close"].diff().fillna(0).clip(upper=0).abs()
    data["RSI"] = 100 - (
        100 / (1 + data["Gains"].rolling(window=window).mean()
               / data["Losses"].rolling(window=window).mean())
    )

    # Drop the warm-up period where RSI isn't valid yet
    return data.iloc[window:]






import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np

def stock_picker():
    stock = input("Enter stock here ... ").strip().upper()
    return stock

def moving_average_calculator(stock):
    # Pull ~1 year of data so the 200-day MA has enough history to populate
    data = yf.download(stock, period="5y")

    if data.empty is True:
        print("No stock found")
        return None

    # Calculate moving averages
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()


    plt.figure(figsize=(12, 6),facecolor='lightgray')
    plt.plot(data['Close'], label='Close Price', alpha=0.9)
    plt.plot(data['SMA50'], label='50-Day SMA')
    plt.plot(data['SMA200'], label='200-Day SMA')
    plt.title(f"{stock} - 50 Day vs 200 Day Moving Average")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Get latest values (drop NaNs in case of insufficient history)
    latest_sma50 = data['SMA50'].dropna().iloc[-1]
    latest_sma200 = data['SMA200'].dropna().iloc[-1]

    if latest_sma50 > latest_sma200:
        result = "Short term bullish (SMA50 > SMA200)"
    elif latest_sma200 > latest_sma50:
        result = "Short term bearish (SMA200 > SMA50)"
    else:
        result = "Equal"
    ## maybe change it so that its if they are a certain percentage away from each other then it is bullish or bearish

    print(f"SMA50: {latest_sma50:.2f}, SMA200: {latest_sma200:.2f}")
    print(f"{result}")

    return result

def relative_strength_index(stock):
    data=yf.download (stock, period="2y", interval="1d")
    print(data)
    if (data.empty):
        print("No stock found")
        return None

    data["Gains"]= data["Close"].diff().fillna(0).clip(lower=0  )

    data["Losses"]= data["Close"].diff().fillna(0).clip(upper=0).abs()
    data["RSI"]= 100-((100)/(1+data["Gains"].rolling (window=14).mean()/data["Losses"].rolling(window=14).mean()))
    print (data)
    return data.iloc[14:]


if __name__ == "__main__":
    ticker = stock_picker()
    relative_strength_index(ticker)

## headlines
## when is next earnign report
##pe
## price target and analyst rating
## compare next stock
## pe

## take derivative of SMA50 and SMA200 to find if they are going to intersect
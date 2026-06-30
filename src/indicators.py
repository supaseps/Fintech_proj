import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

def stock_picker():
    stock = input("Enter stock here ... ").strip().upper()
    data = yf.download(stock, period="5y")

    if data.empty is True:
        print("No stock found")
        return None

    return stock

def moving_average_calculator(stock):
    data = yf.download(stock, period="5y")

    if data.empty is True:
        print("No stock found")
        return None

    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()



    latest_sma50 = data['SMA50'].dropna().iloc[-1]
    latest_sma200 = data['SMA200'].dropna().iloc[-1]

    if latest_sma50 > latest_sma200:
        result = "Short term bullish (SMA50 > SMA200)"
    elif latest_sma200 > latest_sma50:
        result = "Short term bearish (SMA200 > SMA50)"
    else:
        result = "Equal"
    ## maybe change it so that its if they are a certain percentage away from each other then it is bullish or bearish



    return data, result

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

def get_earning_date(stock):
    calendar = yf.Calendars(start=datetime.now(), end=datetime.now() + timedelta(days=365))

    date = yf.Ticker(stock).calendar.get("Earnings Date")   #company's earning date

    broad_market_events = yf.Calendars().get_earnings_calendar(
    start=datetime.now().date(),
    end=datetime.now().date() + timedelta(days=30)
    )  # for next 30 days

    market_events = broad_market_events


    return (date[0] if date is not None else None), market_events



if __name__ == "__main__":
    ticker = stock_picker()
    get_earning_date(ticker)
    

## headlines
##pe
## price target and analyst rating
## compare next stock
## pe


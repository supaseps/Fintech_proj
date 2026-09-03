import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import pandas as pd


def stock_picker(stock=None):
    if stock is None:
        stock = input("Enter stock here ... ").strip().upper()

    data = yf.download(stock, period="5y", interval="1d")

    if data.empty is True:
        print("No stock found")
        return None

    return stock , data

def moving_average_calculator(stock,data):
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

def relative_strength_index(stock,data):
    if (data.empty):
        print("No stock found")
        return None

    data["Gains"]= data["Close"].diff().fillna(0).clip(lower=0  )

    data["Losses"]= data["Close"].diff().fillna(0).clip(upper=0).abs()
    data["RSI"]= 100-((100)/(1+data["Gains"].rolling (window=14).mean()/data["Losses"].rolling(window=14).mean()))

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

def get_pe(stock):
    ticker = yf.Ticker(stock)
    pe_trailing = ticker.info.get("trailingPE")
    pe_forward = ticker.info.get("forwardPE")
    return pe_trailing, pe_forward

def get_price_target (stock):
    ticker= yf.Ticker(stock).info
    price_mean = ticker.get("targetMeanPrice")
    price_high = ticker.get("targetHighPrice")
    price_low = ticker.get("targetLowPrice")
    return price_mean, price_high, price_low

def Average_Directional_Index(stock,data):
    data["True_Range"] = np.maximum(
        data["High"] - data["Low"],
        np.maximum(
            abs(data["High"] - data["Close"].shift(1)),
            abs(data["Low"] - data["Close"].shift(1))
    ))    
    data["Average_True_Range"] = data["True_Range"].rolling(window=14).mean()
    data["H-ph"]=data["High"]-data["High"].shift(1)
    data["L-ph"]=-data["Low"]+data["Low"].shift(1)
    data["+DX"]= np.where((data["H-ph"]>data["L-ph"]) & (data["H-ph"]>0), data["H-ph"], 0)
    data["-DX"]= np.where((data["L-ph"]>data["H-ph"]) & (data["L-ph"]>0), data["L-ph"], 0) 

    data["Smooth_+DX"]=data["+DX"].rolling(window=14).mean()
    for i in range (14, len(data)):
        data["Smooth_+DX"].iloc[i] = (data["Smooth_+DX"].iloc[i-1]*13 + data["+DX"].iloc[i])/14

    data["Smooth_-DX"]=data["-DX"].rolling(window=14).mean()
    for i in range (14, len(data)):
        data["Smooth_-DX"].iloc[i] = (data["Smooth_-DX"].iloc[i-1]*13 + data["-DX"].iloc[i])/14
    
    data["+DMI"]=data["Smooth_+DX"]/data["Average_True_Range"]*100
    data["-DMI"]=data["Smooth_-DX"]/data["Average_True_Range"]*100
    data["DX"]=abs(data["+DMI"]-data["-DMI"])/(data["+DMI"]+data["-DMI"])*100

    data["ADX"]=data["DX"].rolling(window=14).mean()
    for i in range (14, len(data)):
        data["ADX"].iloc[i] = (data["ADX"].iloc[i-1]*13 + data["DX"].iloc[i])/14

    latest_adx = data["ADX"].iloc[-1]
    if pd.isna(latest_adx):
        signal = "ADX is not available because there is insufficient data."
    elif latest_adx < 20:
        signal = "Weak trend / sideways market"
    elif latest_adx < 25:
        signal = "Trend may be starting"
    elif latest_adx < 50:
        signal = "Strong trend"
    elif latest_adx < 75:
        signal = "Very strong trend"
    else:
        signal = "Extremely strong trend"
    

    return data["ADX"], data["+DMI"], data["-DMI"], signal


if __name__ == "__main__":
    stock, data = stock_picker()
    Average_Directional_Index(stock, data)
    

## headlines
## compare next stock
## make ATR separate
##Linear Regression Channel 


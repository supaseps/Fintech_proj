import yfinance as yf

def stock_picker():
    stock = input ("Enter stock here ... ").strip().upper()
    return stock

def moving_average_calculator(stock):
    
    data = yf.download("AAPL", period="2y", interval="1d")

    # Calculate the 200-day moving average using Close prices
    data['SMA_200'] = data['Close'].rolling(window=200).mean()


    print(data[['Close', 'SMA_200']].tail())


stock= stock_picker()
moving_average_calculator(stock)
## headlines
## when is next earnign report
##pe
## price target and analyst rating
## compare next stock
## pe
import cro
import json
import time
import requests
import pandas as pd

with open("keys.json") as keys:
    information = json.load(keys)
    cro.API_KEY = information['api_key']
    cro.SECRET_KEY = information['secret_key']

cro.coinName = 'DOGE'
cro.coinCurrency = 'USDT'
cro.period = '1m'


accountSummary = cro.getAccountSummary()
coinAvailable = accountSummary[accountSummary['currency'] == cro.coinName]['available'].values[0]
usdtAvailable = accountSummary[accountSummary['currency'] == cro.coinCurrency]['available'].values[0]


def entry(close, amt):
    accountSummary = cro.getAccountSummary()
    usdtAvailable = accountSummary[accountSummary['currency'] == cro.coinCurrency]['available'].values[0]

    if usdtAvailable > (close*amt):
        cro.entryOrder(close, amt)
    else:
        amt = usdtAvailable/close
        cro.entryOrder(close, amt)

def exit(close, amt):
    accountSummary = cro.getAccountSummary()
    coinAvailable = accountSummary[accountSummary['currency'] == cro.coinName]['available'].values[0]
    if coinAvailable > amt:
        cro.exitOrder(close, amt)
    else:
        cro.exitOrder(close, coinAvailable)



def trade():

    #obtain updated data
    data = json.loads(requests.get(cro.BASE_URL + f"public/get-candlestick?instrument_name={cro.ticker}&timeframe={cro.period}").text)['result']['data']
    coinData = pd.json_normalize(data)
    coinData = coinData.rename(columns={'t':'Datetime', 'o':'Open', 'h':'High', 'l':'Low', 'c':'Close', 'v':'Volume'})
    coinData['Datetime'] = pd.to_datetime(coinData['Datetime'], unit='ms')
    cro.obtainIndicators(coinData)
    newData = coinData.iloc[-1]
    close = newData['Close']
    rsi = newData['RSI']
    upper = newData['UpperBand']
    lower = newData['LowerBand']
    sma20 = newData['20-SMA']
    sma50 = newData['50-SMA']

    print(close, upper, lower, rsi, sma20, sma50)

    # Implement your own strategy
    #The increase and decrease in prices for entry and exit is an attempt to overcome slippage, which I am still struggling to work around
    if rsi <= 30 and close <= lower or rsi < 20:
        entry(close*1.05, 10)
    elif rsi >= 70 and close >= upper or rsi > 80:
        exit(close*0.95, 20)
    else:
        pass


while True:
    trade()
    time.sleep(30)
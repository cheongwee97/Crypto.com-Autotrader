from locale import currency
import pandas as pd
import json
import time
import hashlib
import hmac
import requests


BASE_URL = "https://api.crypto.com/v2/"
API_KEY = ""
SECRET_KEY = ""
coinName = "DOGE"
coinCurrency = "USDT"
ticker = f"{coinName}_{coinCurrency}"
period = "1m"


# Provided by Crypto.com documentation

MAX_LEVEL = 3

def params_to_str(obj, level):
    if level >= MAX_LEVEL:
        return str(obj)

    return_str = ""
    for key in sorted(obj):
        return_str += key
        if isinstance(obj[key], list):
            for subObj in obj[key]:
                return_str += params_to_str(subObj, ++level)
        else:
            return_str += str(obj[key])
    return return_str

#######################################################################

def getAccountSummary():

    req = {
        "id": 14,
        "method": "private/get-account-summary",
        "api_key": API_KEY,
        "params": {},
        "nonce": int(time.time() * 1000)
    }

    # First ensure the params are alphabetically sorted by key
    param_str = ""

    if "params" in req:
        param_str = params_to_str(req['params'], 0)

    payload_str = req['method'] + str(req['id']) + req['api_key'] + param_str + str(req['nonce'])

    req['sig'] = hmac.new(
        bytes(str(SECRET_KEY), 'utf-8'),
        msg=bytes(payload_str, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    accountSummary = requests.post(BASE_URL+"private/get-account-summary", json=req, headers={'Content-type':'application/json'})

    accountSummary =  pd.json_normalize(json.loads(accountSummary.text)['result']['accounts'])

    return accountSummary

def get_candlestick(instrument_name, period):
    informations = requests.get(BASE_URL + f"public/get-candlestick?instrument_name={instrument_name}&timeframe={period}")
    informations = pd.read_csv(informations.content)
    return informations


def obtainIndicators(stock):
    # Calculating the Indicators

    # Simple Moving Averages
    # Calculate 20-day-SMA
    stock['20-SMA'] = stock['Close'].rolling(window=20).mean()

    # Calculating 50-day-SMA
    stock['50-SMA'] = stock['Close'].rolling(window=50).mean()

    # Calculating the 20-day-std
    std = stock['Close'].rolling(window=20).std()

    # Bollinger Bands
    # Calculating the UpperBand
    stock['UpperBand'] = stock['20-SMA'] + (2*std)

    #Calculating the LowerBand
    stock['LowerBand'] = stock['20-SMA'] - (2*std)

    # RSI
    # calculating delta (difference of closing price from prev day closing price)
    delta = stock['Close'].diff()
    # Extracting positive delta
    up = delta.clip(lower=0)
    # Extracting negative delta
    down = abs(delta.clip(upper=0))
    # Calculating average gain, usually over 14days
    avgGain = up.rolling(window=14).mean()
    # Calculating average loss
    avgLoss = down.rolling(window=14).mean()
    # RSI
    rs = avgGain/avgLoss
    stock['RSI'] = 100-(100/(1+rs))

    return stock.dropna(inplace=True)

def entryOrder(close, amt=10):
    req = {
            "id": 11,
            "method": "private/create-order",
            "api_key": API_KEY,
            "params": {
                "instrument_name": ticker,
                "side": "BUY",
                "type": "LIMIT",
                "price": close,
                "quantity": amt,
                "time_in_force": "GOOD_TILL_CANCEL",
                "exec_inst": "POST_ONLY"
                },
            "nonce": int(time.time() * 1000)
            }

    # First ensure the params are alphabetically sorted by key
    param_str = ""


    if "params" in req:
        param_str = params_to_str(req['params'], 0)

    payload_str = req['method'] + str(req['id']) + req['api_key'] + param_str + str(req['nonce'])

    req['sig'] = hmac.new(
        bytes(str(SECRET_KEY), 'utf-8'),
        msg=bytes(payload_str, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    entryPost = requests.post(BASE_URL+"private/create-order", json=req, headers={'content-type':'application/json'})
    print(f"Entry @ {close} * {amt}")
    return entryPost

def exitOrder(close, amt=5):
    req = {
        "id": 11,
        "method": "private/create-order",
        "api_key": API_KEY,
        "params": {
            "instrument_name": ticker,
            "side": "SELL",
            "type": "LIMIT",
            "price": close,
            "quantity": amt,
            "time_in_force": "GOOD_TILL_CANCEL",
            "exec_inst": "POST_ONLY"
        },
        "nonce": int(time.time() * 1000)
        }

    # First ensure the params are alphabetically sorted by key
    param_str = ""


    if "params" in req:
        param_str = params_to_str(req['params'], 0)

    payload_str = req['method'] + str(req['id']) + req['api_key'] + param_str + str(req['nonce'])

    req['sig'] = hmac.new(
        bytes(str(SECRET_KEY), 'utf-8'),
        msg=bytes(payload_str, 'utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    exitPost = requests.post(BASE_URL+"private/create-order", json=req, headers={'Content-type':'application/json'})
    
    print(f"Exit @ {close} * {amt}")
    return exitPost
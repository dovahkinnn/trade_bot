# libraries
from binance.client import Client
from binance.enums import *
import talib as ta
from talib import MA_Type
import numpy as np
import time
import smtplib
from os import system

# define our clear function
def Clear():
    system('cls')
    print("~"*30)

# data collect
def CollectData(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        close = [float(entry[4]) for entry in klines]
        close_array = np.array(close, dtype=float)
    except Exception as exp:
        print(exp.status_code)
        print(exp.message)
        
        CollectData(symbol)
    
    return close_array

# rsi
def RSI(arr):
    rsi = ta.RSI(arr, timeperiod=14)
    return rsi[-1]

# macd
def MACD(close_array):
    macd, macdsignal, macdhist = ta.MACD(close_array, fastperiod=12, slowperiod=26, signalperiod=9)
    return macd, macdsignal, macdhist

# bb
def BBL(close_array):
    bbupper, bbmiddle, bblower = ta.BBANDS(
                            close_array, 
                            timeperiod=20,
                            nbdevup=2,
                            nbdevdn=0,
                            matype=0)
    
    bbMiddlePrice = float(bbmiddle[-1])
    bbUpperPrice = float(bbupper[-1])
    bbLowerPrice = bbMiddlePrice - (bbUpperPrice-bbMiddlePrice)  

    return bbUpperPrice, bbMiddlePrice, bbLowerPrice

# get balance
def GetBalance(coin):
    balance = client.get_asset_balance(asset=coin)
    
    return float(balance['free'])

# get price
def GetPrice(coin):
    price = client.get_ticker(symbol=coin)

    return float(price['askPrice'])

# get all coins
def GetCoinList():
    info = client.get_all_tickers()
    allCoins = [entry['symbol'] for entry in info]
    usdtCoins = []

    for i in allCoins:
        if i[-4:] == 'USDT':
            usdtCoins.append(i)
    return usdtCoins

################################################################### SETTINGS
# connection
client = Client(api_key, secret_key)

# configurations
interval = '1m'
limit = 500

# define list
defaultCoinList = ["PNTUSDT"]
coinList = defaultCoinList

################################################################### LOOP
stat = "buy"
enterPrice = float(0.0)
while True:
    try:
        for i in coinList:

            # get datas
            datas = CollectData(i)
            # get price
            price = GetPrice(i)
            # get bb values
            bbupper, bbmiddle, bblower = BBL(datas)
            macd, macdsignal, macdhist = MACD(datas)

            last_macd = macd[-2]
            last_macd_signal = macdsignal[-2]
            previous_macd = macd[-3]
            previous_macd_signal = macdsignal[-3]

            macd_cross_up = last_macd > last_macd_signal and previous_macd < previous_macd_signal
            macd_cross_down = last_macd < last_macd_signal and previous_macd > previous_macd_signal

            trades = client.get_my_trades(symbol=i)
            if trades:
                son = trades[-1]["price"]
                son = float(son)

            balanceUsdt = GetBalance('USDT')
            if stat == "buy":
                if macd_cross_up:
                    test = balanceUsdt / price
                    test = test*(999/1000)
                    test = float(format(test,'.2f'))
                    
                    client.order_market_buy(
                        symbol = i,
                        quantity = test
                    )
                    
                    stat = "oco"
                    coinList = [i]
                    ocoPrice = price
                    
                    time.sleep(3)

                else:
                    Clear()
                    print("Holding: USDT")
                    print("Balance:",balanceUsdt)
                    print("Symbol:",i)
                    print("Price:",price)
                    print("BBLower:",bblower)
                    print("~"*30)

            elif stat == "sell":
                stoploss = son-(son*0.5/100)
                balance = GetBalance(i[:-4])
                balance= balance*(999/1000)
                balance = float(format(balance,'.2f'))
                if macd_cross_down :
                    ocoPrice = price
                    stat = "oco"

                elif price  <= stoploss:
                    
                    client.order_market_sell(
                        symbol = i,
                        quantity = balance
                    )
                    
                    stat = "stop"
                    coinList = [i]

                    time.sleep(3)

                else:
                    Clear()
                    print("Holding:",i)
                    print("Balance:",balance)
                    print("Symbol:",i)
                    print("Enter Price:",enterPrice)
                    print("Price:",price)
                    print("BBMiddle:",bbmiddle)
                    print("Stop Loss:",stoploss)
                    print("~"*30)

            elif stat == "stop":
                if price  >= bbmiddle :
                    stat = "buy"
                    coinList = defaultCoinList
                    
                else:
                    Clear()
                    print("STOP LOSE WAITING...")
                    print("Holding: USDT")
                    print("Balance:",balanceUsdt)
                    print("Symbol:",i)
                    print("Price:",price)
                    print("BBMiddle:",bbmiddle)
                    print("~"*30)

            elif stat == "oco":
                oco = ocoPrice+(ocoPrice*0.5/100)

                balance = GetBalance(i[:-4])
                balance= balance*(999/1000)
                balance = float(format(balance,'.2f'))

                if price < ocoPrice:
                    client.order_market_sell(
                        symbol = i,
                        quantity = balance
                    )

                    stat = "buy"
                    coinList = defaultCoinList

                    time.sleep(3)

                elif price >= oco:
                    ocoPrice = oco

                else:
                    Clear()
                    print("Holding:",i)
                    print("Balance:",balance)
                    print("Symbol:",i)
                    print("Price:",price)
                    print("OCO Price:",ocoPrice)
                    print("OCO Target:",oco)
                    print("~"*30)
                    
    except Exception as inst:
        Clear()
        print("HATA:",inst)
        time.sleep(5)

# -*- coding: utf-8 -*-
"""
create a strategy

Created on Tue May 17 12:48:18 2022
@author: jewittj
"""
from ibapi.wrapper import EWrapper 
from ibapi.client import EClient 
from ibapi.contract import Contract 
from ibapi.order import Order as order 
import pandas as pd 
import threading 
import datetime as dt
import warnings
import time as t
warnings.simplefilter(action='ignore', category=FutureWarning)

class Bot( EWrapper,EClient ):
    def __init__( self ):
        EClient.__init__( self,self )
        self.ohlcv = pd.DataFrame( columns=["time",'open','high','low','close','volume'] )
        self.f = False
    def realtimeBar( self,reqId,time,open_,high,low,close,volume,wap,count ):
        super().realtimeBar( reqId,time,open_,high,low,close,volume,wap,count )
        ti = dt.datetime.fromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
        d = {"time":ti,"open":open_,"high":high,"low":low,"close":close,"volume":volume } 
        self.ohlcv = self.ohlcv.append( d, ignore_index=True ) 
        
def connect(): 
    bot.run()

def usTechStk(symbol,sec_type="STK",currency="USD",exchange="ISLAND"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

def frame( bot_object,tkr ):
    df = bot_object.ohlcv
    #df.set_index( "time",inplace=True )
    return df 


def live_data( Contract ):
    bot.reqRealTimeBars( reqId=0,contract=Contract,barSize=5,whatToShow="TRADES",useRTH=0,realTimeBarsOptions="" )

bot = Bot()
bot.connect( host='127.0.0.1',port=7497,clientId=11 ) 
con_thread = threading.Thread( target=connect,daemon=True )
con_thread.start()

ticker = "AMC" 


start = t.time()
print(start)
fin = t.time() + 10 #60*60*3
print(fin)



live_data(usTechStk(ticker))
    
def stat( df_) :
    df = df_ 
    ti      =df["time"]
    op_     =df["open"]
    hi      =df["high"]
    lo      =df["low"]
    clse    =df["close"]
    vol     =df["volume"]
    return ti,op_,hi,lo,clse,vol

# main():
while t.time() <= fin:
    ohlcv_ = pd.DataFrame( columns=["time",'open','high','low','close','volume'] )
    ohlcv = bot.ohlcv
    ti,op_,hi,lo,cle,vol = stat( ohlcv )
  



print(ohlcv)

# -*- coding: utf-8 -*-
"""
IB API Template

Created on 
Sun May 8 05:48:58 2022
@author: jewittj
"""

#<<<<<<<<<<<<<<<<<<< imports >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

import threading     # needed to create multiple threads (function connect will run in background)
import time          # for creating pauses between connect, etc for purpose of stopping overlap

import numpy as np                    # ?
import pandas as pd                   # need dataframes to sort incoming data

from ibapi.client import EClient as Client               # server requests 
from ibapi.wrapper import EWrapper as Wrapper            # translate/recieve incoming
from ibapi.contract import Contract
from ibapi.order import Order 



#<<<<<<<<<<<<<<<<<<< bot >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class Bot( Client,Wrapper ):
    def __init__( self ):               # initializing with following properties 
        Client.__init__( self,self )    # inheriting EClient functions
        self.data = {}                  # create usable data dictionary 
        
    def historicalData( self,req,bar ):             # create dataframe per bar,request,bar
        'returns the requested historical data'
        if req not in self.data:                    # if reqid attribute not already created 
            self.data[req] = [{"Date":bar.date,     # data dict number holding dictionary
                               "Open":bar.open,     # of bar data 
                               "High":bar.high,
                               "Low":bar.low,
                               "Close":bar.close,
                               "Volume":bar.volume}]
        else: 
            self.data[req].append({"Date":bar.date, # if already created, adding to
                                   "Open":bar.open,
                                   "High":bar.high,
                                   "Low":bar.low,
                                   "Close":bar.close,
                                   "Volume":bar.volume})
        #print("req:{}, date:{}, open:{}, high:{}, low:{}, close:{}, volume:{}".format(req,bar.date,bar.open,bar.high,bar.low,bar.close,bar.volume))
            
            
def stk( sym,sec_type='STK',cur='USD',exc='ISLAND' ):    # template for equity parameters 
    tkr = Contract()
    tkr.symbol = sym
    tkr.secType = sec_type
    tkr.currency = cur
    tkr.exchange = exc
    return tkr

def get_data( req,tkr,tmbk,cndl ):            # request bar data, returns w/ EWrapper.historicaldata  
    bot.reqHistoricalData( reqId=req,contract=tkr,endDateTime='',
                           durationStr=tmbk,barSizeSetting=cndl,
                           whatToShow='ADJUSTED_LAST',useRTH=1,
                           formatDate=1,keepUpToDate=0,chartOptions=[] )
        
def socket():         # will become background (daemon) thread, server connection 
    bot.run()         # Client method = "This is the function that has the message loop."

bot = Bot()                                                   # instantiate bot from Bot class 
bot.connect( host='127.0.0.1',port=7497,clientId=1 )          # init server connection 7497=sim,7496=live
srv_con = threading.Thread( target=socket,daemon=True )     # init server connection thread to run in background
srv_con.start()                                             # start background server connect
time.sleep(1)                                                 # allow con space to initialize 


tkrs = [ 'AMC','TSLA','FB' ]                                 # will eventually be replaced w/ scannner 
for tkr in tkrs:                                            # loop through found equities 
    get_data( tkrs.index(tkr),stk(tkr),'2 Y','1 day' )      # retrieve data w/ set param
    time.sleep(1)                                             # allow time to retrieve data
    

def data_frame( tkrs,bot_obj ):                       # create historical data dataframe to pass to indicators
    df_data = {}                                     # store dataframes in dictionary
    for tkr in tkrs:                                                   # loop through equities
        df_data[tkr] = pd.DataFrame( bot_obj.data[tkrs.index(tkr)] )    # create dataframe with data dict
        df_data[tkr].set_index( 'Date',inplace=True )                 # set index as data
    return df_data

hist = data_frame( tkrs, bot )
    
def CAGR( df ):

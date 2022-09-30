# -*- coding: utf-8 -*-
"""
trading bot 

Created on Thu May 19 07:36:49 2022
@author: jewittj

"""

# IMPORTS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ibapi.wrapper import EWrapper 
from ibapi.client import EClient 
from ibapi.contract import Contract
from ibapi.order import Order
import pandas as pd 
import numpy as np 
import threading                             
import time as t
import datetime as dt 
import time as t
import warnings
import matplotlib.pyplot as pyp
from talib import MACD as macdSignalHistogram
from talib import ATR as averageTrueRange
from talib import EMA as exponentialMovingAverage 
from talib import ADX as averageDirectionalIndex
from talib import LINEARREG_SLOPE as linearRegressionSlope
warnings.simplefilter( action='ignore',category=FutureWarning )




# BOT CLASS >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class Bot( EWrapper,EClient ):
    def __init__( self ):
        EClient.__init__( self,self ) 
        
        self.pastOHLCVs    = {}
        self.newOHLCV      = [] 
        self.newOHLCVlist  = []        

    def historicalData( self,reqId,bar ):
        # print( bar.date[-8:]," ",bar.close )
        if reqId not in self.pastOHLCVs:                   
            self.pastOHLCVs[reqId] = [{ 'time':bar.date[-8:].replace(':',''),'open':bar.open,'high':bar.high,
                                        'low':bar.low,'close':bar.close,'volume':bar.volume }]
        else: 
            self.pastOHLCVs[reqId].append({ 'time':bar.date[-8:].replace(':',''),'open':bar.open,'high':bar.high,
                                            'low':bar.low,'close':bar.close,'volume':bar.volume })

    def realtimeBar( self,reqId,time,open_,high,low,close,volume,wap,count ):
        super().realtimeBar( reqId,time,open_,high,low,close,volume,wap,count )
        self.newOHLCV = { 'time':dt.datetime.fromtimestamp(time).strftime('%H%M%S'),'open':open_,'high':high,'low':low,'close':close,'volume':volume }  
        print( "> bar recieved at "+str(self.newOHLCV["time"][:2] + ":" + self.newOHLCV["time"][2:4] + ":" + self.newOHLCV["time"][4:] ) +"  "+str(self.newOHLCV['close']) )
        self.newOHLCVlist.append( self.newOHLCV )

    def nextValidId( self,orderId ):         
        super().nextValidId( orderId )
        self.nextValidOrderId = orderId
        print( "NextValidId:", orderId )
        
        
        
# UTILITIES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def connect(): 
    bot.run() 
    
def getLiveTwelfths( contract ):                  
    bot.reqRealTimeBars( reqId=0,contract=contract,        
                         barSize=5,whatToShow="TRADES",
                         useRTH=0,realTimeBarsOptions="" )     

def toStock( symbol,sec_type="STK",currency="USD",exchange="ISLAND" ):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type                  
    contract.currency = currency
    contract.exchange = exchange
    return contract

def getHistLength():
    fourAM = 40000 
    now = dt.datetime.now()
    now = now.strftime("%H%M%S")
    sincefourAM = int(now)-int(fourAM)
    sincefourAM = str(sincefourAM).rjust(6,'0')
    since4InSecs = int(sincefourAM[0:2])*60*60 + int(sincefourAM[2:4])*60 + int(sincefourAM[-2:])
    maxLookBackSecs = 86400
    if since4InSecs < maxLookBackSecs :
        since4InSecs = str(since4InSecs)+" S"
        return since4InSecs
    else : 
        maxLookBackSecs = str(maxLookBackSecs)+" S"
        return maxLookBackSecs

def getHistBars( req_num,contract,duration,candle_size ):
    bot.reqHistoricalData( reqId=req_num,contract=contract,
                           endDateTime='',durationStr=duration,
                           barSizeSetting=candle_size,whatToShow='ADJUSTED_LAST',
                           useRTH=0,formatDate=1,
                           keepUpToDate=0,chartOptions=[] )

   
          
    
# STUDIES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def macd( bDF,liveBar=None ):        
    if liveBar:
        bDF.iloc[-1]['macd'],bDF.iloc[-1]['signal'],bDF.iloc[-1]['histogram'] = macdSignalHistogram( bDF.iloc[-27:-1]['close'] )[2][-1:]
    else : 
        bDF['macd'],bDF['signal'],bDF['histogram'] = macdSignalHistogram( bDF['close'] )
    return bDF
                                                                                                            
def atr( bDF,liveBar=None ):  
    if liveBar:
        bDF.iloc[-1,'atr'] = averageTrueRange( bDF.iloc[-1]['high'],bDF.iloc[-1]['low'],bDF.iloc[-1]['close'], 14 )
    else:
        bDF['atr'] = averageTrueRange( bDF['high'],bDF['low'],bDF['close'], 14 )
    return bDF

def ema( bDF,liveBar=None  ):
    if liveBar:
        bDF.iloc[-1,'ema'] = exponentialMovingAverage( bDF.iloc[-1,'close'],9 )
    else:
        bDF['ema'] = exponentialMovingAverage( bDF['close'],9 )
    return bDF 

def keltchan( bDF,liveBar=None,multiplier=2  ): 
    if liveBar:
        bDF.iloc[-1,'up band'] = bDF.iloc[-1,'ema'] + multiplier * bDF.iloc[-1,'atr']
        bDF.iloc[-1,'low band'] = bDF.iloc[-1,'ema'] - multiplier * bDF.iloc[-1,'atr']
    else:
        bDF['up band'] = bDF['ema'] + multiplier * bDF['atr']
        bDF['low band'] = bDF['ema'] - multiplier * bDF['atr']
    return bDF

def adx( bDF,liveBar=None ): 
    bDF["adx"] = averageDirectionalIndex( bDF['high'], bDF['low'], bDF['close'] )
    return bDF

def linReg( bDF ):
    try:
        bDF["linear regression histogram"] = linearRegressionSlope( bDF['histogram'],2 ) 
    except Exception as e: print( e )
    return bDF

def marketToLimit( action,quantity ):
    order                = Order()
    order.action         = action
    order.orderType      = "MTL"
    order.totalQuantity  = quantity
    return order
    
def limitOrder( action,quantity,price ):
    order               = Order() 
    order.action        = action 
    order.orderType     = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice      = price
    return order




# MARKET CONNECT / MAKE HISTORICAL BAR DATAFRAME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

bot = Bot()                                                           
bot.connect( host='127.0.0.1',port=7496,clientId=1 )                 
con_thread = threading.Thread( target=connect,daemon=True )      
con_thread.start()                                              

ticker     = "AMC"
#ticker      = "SQQQ"
ticker      = toStock( ticker )

liveStream  = getLiveTwelfths( ticker )
studies     = [ adx,ema,atr,keltchan,macd,linReg ]     

howFarBack  = getHistLength() 
getTwelfths = getHistBars(  12,ticker,howFarBack,'5 secs'   ) 
getFourths  = getHistBars(  4,ticker,howFarBack,'15 secs'   ) 
getOnes     = getHistBars(  1,ticker,howFarBack,'1 min'     ) 
getFives    = getHistBars(  5,ticker,howFarBack,'5 mins'    ) 
getFifteens = getHistBars(  15,ticker,'3 D','15 mins'       )

t.sleep(5)

twelfths    = pd.DataFrame( bot.pastOHLCVs[12] )              #
fourths     = pd.DataFrame( bot.pastOHLCVs[4]  )              
ones        = pd.DataFrame( bot.pastOHLCVs[1]  )              #
fives       = pd.DataFrame( bot.pastOHLCVs[5]  )              # 
fifteens    = pd.DataFrame( bot.pastOHLCVs[15] )
      
intervals   = [ twelfths,fourths,ones,fives,fifteens ]

for i in range(len( intervals )):
    for s in range(len( studies )):
        intervals[i] = studies[s]( intervals[i] )




# CONTINUALLY APPEND LIVE BARS TO HISTORICAL DATA DATAFRAMES >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Now          = int( dt.datetime.now().strftime("%H%M%S" ))
marketClose  = 160000
timeGap      = True

while Now < marketClose :
    if int(bot.newOHLCVlist[-1]['time']) - int(twelfths.iloc[-1]['time']) == 5: timeGap = False
    else: timeGap = True
    
    if timeGap == False:
        if int(bot.newOHLCVlist[-1]['time']) - int(twelfths.iloc[-1]['time']) == 5:
            twelfths = twelfths.append( bot.newOHLCV,ignore_index=True )      
            for s in range(len( studies )): 
                twelfths = studies[s]( twelfths )
            print( "> built new twelfth... ",twelfths.iloc[-1]["time"][:2] + ":" + twelfths.iloc[-1]["time"][2:4] + ":" + twelfths.iloc[-1]["time"][4:] )
                
            if(( twelfths.iloc[-3]['time'][4:] == "00" and twelfths.iloc[-2]['time'][4:] == "05" and twelfths.iloc[-1]['time'][4:] == "10" ) or 
               ( twelfths.iloc[-3]['time'][4:] == "15" and twelfths.iloc[-2]['time'][4:] == "20" and twelfths.iloc[-1]['time'][4:] == "25" ) or 
               ( twelfths.iloc[-3]['time'][4:] == "30" and twelfths.iloc[-2]['time'][4:] == "35" and twelfths.iloc[-1]['time'][4:] == "40" ) or 
               ( twelfths.iloc[-3]['time'][4:] == "45" and twelfths.iloc[-2]['time'][4:] == "50" and twelfths.iloc[-1]['time'][4:] == "55" )) :
                    newFourth = [{ 'time'  : twelfths.iloc[-3]['time'],
                                   'open'  : twelfths.iloc[-3]["open"],
                                   'high'  : max( twelfths[-3:-1]["high"] ), 
                                   "low"   : min( twelfths[-3:-1]["low"] ), 
                                   "close" : twelfths.iloc[-1]['close'],
                                   "volume": sum( twelfths[-3:-1]["volume"] )  }]
                    fourths = fourths.append( newFourth,ignore_index=True )
                    for s in range(len( studies )): 
                        fourths = studies[s]( fourths )
                    print( "  > built new fourth...  ",fourths.iloc[-1]["time"][:2] + ":" + fourths.iloc[-1]["time"][2:4] + ":" + fourths.iloc[-1]["time"][4:] )
                        
                    if twelfths.iloc[-1]['time'][4:] == "55" and ones.iloc[-12]['time'][4:] == "00":
                        newOne = [{ "time"  : twelfths.iloc[-12]['time'],
                                    "open"  : twelfths.iloc[-12]["open"],
                                    "high"  : max( twelfths[-12:-1]["high"]), 
                                    "low"   : min( twelfths[-12:-1]["low"]),
                                    "close" : twelfths.iloc[-1]['close'],
                                    "volume": sum( twelfths[-12:-1]["volume"]) }]
                        ones = ones.append( newOne,ignore_index=True )
                        for s in range(len( studies )): 
                            ones = studies[s]( ones )
                        print( "    > built new one at...  ",ones.iloc[-1]["time"][:2] + ":" + ones.iloc[-1]["time"][2:4] + ":" + ones.iloc[-1]["time"][4:] )
                            
                        if int( twelfths.iloc[-1]['time'] ) - int( twelfths.iloc[-60]['time'] ) == 455 and (twelfths.iloc[-60]['time'][3:]=="500" or twelfths.iloc[-60]['time'][3:]=="000"):
                            newFive = [{ "time" : twelfths.iloc[-60]['time'],
                                        "open"  : twelfths.iloc[-60]["open"],
                                        "high"  : max(twelfths[-60:-1]["high"]), 
                                        "low"   : min(twelfths[-60:-1]["low"]),
                                        "close" : twelfths.iloc[-1]['close'],
                                        "volume": sum(twelfths[-60:-1]["volume"]) }]
                            fives = fives.append( newFive,ignore_index=True )
                            for s in range(len( studies )): 
                                fives = studies[s]( fives )
                            print( "      > built new five at... ",fives.iloc[-1]["time"][:2] + ":" + fives.iloc[-1]["time"][2:4] + ":" + fives.iloc[-1]["time"][4:] )
                             
    elif timeGap: 
        for newTwelfth in range(len( bot.newOHLCVlist )):
            if int( bot.newOHLCVlist[newTwelfth]['time'] ) > int( twelfths.iloc[-1]['time'] ):
                    twelfths = twelfths.append( bot.newOHLCVlist[newTwelfth],ignore_index=True )
                    for s in range(len( studies )): 
                        twelfths = studies[s]( twelfths )
                        
                    if(( twelfths.iloc[-3]['time'][4:] == "00" and twelfths.iloc[-2]['time'][4:] == "05" and twelfths.iloc[-1]['time'][4:] == "10" ) or 
                       ( twelfths.iloc[-3]['time'][4:] == "15" and twelfths.iloc[-2]['time'][4:] == "20" and twelfths.iloc[-1]['time'][4:] == "25" ) or 
                       ( twelfths.iloc[-3]['time'][4:] == "30" and twelfths.iloc[-2]['time'][4:] == "35" and twelfths.iloc[-1]['time'][4:] == "40" ) or 
                       ( twelfths.iloc[-3]['time'][4:] == "45" and twelfths.iloc[-2]['time'][4:] == "50" and twelfths.iloc[-1]['time'][4:] == "55" )) :
                            newFourth = [{ 'time'  : twelfths.iloc[-3]['time'],
                                           'open'  : twelfths.iloc[-3]["open"],
                                           'high'  : max( twelfths[-3:-1]["high"] ), 
                                           "low"   : min( twelfths[-3:-1]["low"] ), 
                                           "close" : twelfths.iloc[-1]['close'],
                                           "volume": sum( twelfths[-3:-1]["volume"] )  }]
                            fourths = fourths.append( newFourth,ignore_index=True )
                            for s in range(len( studies )): 
                                fourths = studies[s]( fourths )
                                
                            if twelfths.iloc[-1]['time'][4:] == "55" and ones.iloc[-12]['time'][4:] == "00":
                                newOne = [{ "time"  : twelfths.iloc[-12]['time'],
                                            "open"  : twelfths.iloc[-12]["open"],
                                            "high"  : max( twelfths[-12:-1]["high"]), 
                                            "low"   : min( twelfths[-12:-1]["low"]),
                                            "close" : twelfths.iloc[-1]['close'],
                                            "volume": sum( twelfths[-12:-1]["volume"]) }]
                                ones = ones.append( newOne,ignore_index=True )
                                for s in range(len( studies )): 
                                    ones = studies[s]( ones )
                                    
                                if int( twelfths.iloc[-1]['time'] ) - int( twelfths.iloc[-60]['time'] ) == 455 and (twelfths.iloc[-60]['time'][3:]=="500" or twelfths.iloc[-60]['time'][3:]=="000"):
                                    newFive = [{ "time"  : twelfths.iloc[-60]['time'],
                                                "open"  : twelfths.iloc[-60]["open"],
                                                "high"  : max(twelfths[-60:-1]["high"]), 
                                                "low"   : min(twelfths[-60:-1]["low"]),
                                                "close" : twelfths.iloc[-1]['close'],
                                                "volume": sum(twelfths[-60:-1]["volume"]) }]
                                    fives = fives.append( newFive,ignore_index=True )
                                    for s in range(len( studies )): 
                                        fives = studies[s]( fives )


if noPosition: 

    entrySlope=-0.005
    if(     fives.iloc[-2]["f'(macd diff)"]<=0 
        and fives.iloc[-1]["f'(macd diff)"]>fives.iloc[-2]["f'(macd diff)"]
        and fives.iloc[-1]["f'(macd diff)"]>=entrySlope 
        and fives.iloc[-1]["f'(ROC)"]>0  
        and ives.iloc[-1]["adx"]>15 ):
                                                                                            # define initial entry logic
        if(     ones.iloc[-1]["f'(ROC)"] 
            and ones.iloc[-1]["f'(DI+)"]-ones.iloc[-1]["f'(DI-)"]>0 
            and ones.iloc[-1]["adx"]>15 
            and (ones.iloc[-1]["f'(macd diff)"]>=0 or ones.iloc[-1]["macd diff"]>=0 )):
                                
            whereLimit=twelfth.iloc[-1]["close"]                                            # define entry location
            newBuyOrder=placeLimit( "BUY",num,whereLimit )
        
    else: pass
        
if hasPosition: 
    if(    pnL>=0.10 
        or fives.iloc[-1]["f'(macd diff)"]<fives.iloc[-2]["f'(macd diff)"] ):
        
        whereLimit=twelfth.iloc[-1]["close"]                                            # define entry location
        newSellOrder=placeLimit( "SELL",num,whereLimit )        
                  
                                                                                        
    

                     
'''
ENTER when... 

    If in most recent FIVE MIN... 
    
    1. derivative of macd difference >= -0.001 from one bar ago
        [ finding accumulation period in overextended sell-off ]
    
    2. ROC derivative > 0 from since minimum of macd difference
        [ clarifying trend is coming out of compression period ]
        
    3. ??? adx coming out of minimum 
    
        if in most recent ONE MIN...
        
        3. derivative of ROC from start of 5min
                bar is positive [example, after 5 10:05-10:10 looking for
                         increasing ROC in 10:11,12,13,14,15]
            [ clarifying smaller time interval is pushing out of 
              accumulation period, pushing up ]
        
        4. DI+ > DI- for one bar or about to cross as measured by 
                slope of linReg of DI+ and DI-
                
                linear regression of DI- from one bar ago < 0
                linear regression of DI+ from one bar ago > 0 
                = DI+[linReg] - DI-[linReg] > 0
            
            [ positive trend is beginning to control direction
              or at least taking control ]
                
        5. adx > 15
            [ trend has integrity ]
        
        6. derivative of macd difference >= 0 from one bar ago OR
           macd difference at least above 0
            [ not buying into downward momentum ]
            
            THEN enter at...
            1. limit on 9ema or (9ema or Kelt Chan Bans) +- atr 
            
EXIT ....
PYRAMID ....

NEED:
    Five Min OHLCV, Macd, ROC, 9ema, atr, Keltner Channels   
    One Min OHLCV, Macd, adx, ROC, 9ema, atr, Keltner Channels
    
    
    
    
 '''                                                          
                           
               '''                     
     if( int(fives.iloc[-1]["time"]) >  90000 and int(fives.iloc[-1]["time"]) < 160000 and
          fives.iloc[-1]["adx"] > 15 and fives.iloc[-1]["linear regression histogram"] >= 0 ):
             print("in five minute candle at... ",fives.iloc[-1]["time"][:2] + ":" + fives.iloc[-1]["time"][2:4] + ":" + fives.iloc[-1]["time"][4:]) 
                              
             if ones.iloc[-1]["linear regression histogram"] > 0:
                 print( "    in one minute candle at... ",ones.iloc[-1]["time"][:2] + ":" + ones.iloc[-1]["time"][2:4] + ":" + ones.iloc[-1]["time"][4:]) 
                                      
                 if fourths.iloc[-1]["linear regression histogram"] > 0 and fourths.iloc[-2]["linear regression histogram"] < 0:
                     print( "        in fourth minute candle at... ",fourths.iloc[-1]["time"][:2] + ":" + fourths.iloc[-1]["time"][2:4] + ":" + fourths.iloc[-1]["time"][4:]) 
                                              
                     if twelfths.iloc[-1]["linear regression histogram"] > 0 and twelfths.iloc[-2]["linear regression histogram"] < 0:
                         print( "            in twelfth candle at... ",twelfths.iloc[-1]["time"][:2] + ":" + twelfths.iloc[-1]["time"][2:4] + ":" + twelfths.iloc[-1]["time"][4:] ) 
                         print( ">           open/buy at... ",twelfths.iloc[-1]["open"] )
                                           
                         bot.reqIds(-1)
                         order_id = bot.nextValidOrderId
                         bot.placeOrder( order_id,ticker,marketToLimit("BUY",1 ))
                         t.sleep(1)
                         bot.reqIds(-1)
                         order_id = bot.nextValidOrderId
                         bot.placeOrder( order_id,ticker,limitOrder("SELL",1,twelfths.iloc[-1]["open"] ))
                         '''            
                           
                           
                           
                           
                           getFive    = getHistBars(  11,ticker,'2 D','5 mins'    )
                           five       = pd.DataFrame( bot.pastOHLCVs[11]  )
                           pyp.plot(  ones["close"])
                           
                           
                           
                           five = linReg( five )
                           
                           
                           
                           
    if timeGap: 
        for newTwelfth in range(len( bot.newOHLCVlist )):
            if int( bot.newOHLCVlist[newTwelfth]['time'] ) > int( twelfths.iloc[-1]['time'] ):
                    twelfths = twelfths.append( bot.newOHLCVlist[newTwelfth],ignore_index=True )
                    for s in range(len( studies )): 
                        twelfths = studies[s]( twelfths )
                        
                    if(( twelfths.iloc[-3]['time'][4:] == "00" and twelfths.iloc[-2]['time'][4:] == "05" and twelfths.iloc[-1]['time'][4:] == "10" ) or 
                       ( twelfths.iloc[-3]['time'][4:] == "15" and twelfths.iloc[-2]['time'][4:] == "20" and twelfths.iloc[-1]['time'][4:] == "25" ) or 
                       ( twelfths.iloc[-3]['time'][4:] == "30" and twelfths.iloc[-2]['time'][4:] == "35" and twelfths.iloc[-1]['time'][4:] == "40" ) or 
                       ( twelfths.iloc[-3]['time'][4:] == "45" and twelfths.iloc[-2]['time'][4:] == "50" and twelfths.iloc[-1]['time'][4:] == "55" )) :
                            newFourth = [{ 'time'  : twelfths.iloc[-3]['time'],
                                           'open'  : twelfths.iloc[-3]["open"],
                                           'high'  : max( twelfths[-3:-1]["high"] ), 
                                           "low"   : min( twelfths[-3:-1]["low"] ), 
                                           "close" : twelfths.iloc[-1]['close'],
                                           "volume": sum( twelfths[-3:-1]["volume"] )  }]
                            fourths = fourths.append( newFourth,ignore_index=True )
                            for s in range(len( studies )): 
                                fourths = studies[s]( fourths )
                                
                            if twelfths.iloc[-1]['time'][4:] == "55" and ones.iloc[-12]['time'][4:] == "00":
                                newOne = [{ "time"  : fourths.iloc[-12]['time'],
                                            "open"  : fourths.iloc[-12]["open"],
                                            "high"  : max( fourths[-12:-1]["high"]), 
                                            "low"   : min( fourths[-12:-1]["low"]),
                                            "close" : fourths.iloc[-1]['close'],
                                            "volume": sum( fourths[-12:-1]["volume"]) }]
                                ones = ones.append( newOne,ignore_index=True )
                                for s in range(len( studies )): 
                                    ones = studies[s]( ones )
                                    
                                if int( twelfths.iloc[-1]['time'] ) - int( twelfths.iloc[-60]['time'] ) == 500:
                                    newFive = [{ "time"  : twelfths.iloc[-59]['time'],
                                                "open"  : twelfths.iloc[-59]["open"],
                                                "high"  : max(twelfths[-59:-1]["high"]), 
                                                "low"   : min(twelfths[-59:-1]["low"]),
                                                "close" : twelfths.iloc[-1]['close'],
                                                "volume": sum(twelfths[-59:-1]["volume"]) }]
                                    fives = fives.append( newFive,ignore_index=True )
                                    for s in range(len( studies )): 
                                        fives = studies[s]( fives )
        timeGap = False
    else: 
        pass
                
        
        
        
# BOT TRADE LOGIC  >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        '''
        if( int(fives.iloc[-1]["time"]) >  93000 and int(fives.iloc[-1]["time"]) < 160000 and
                         fives.iloc[-1]["adx"] > 15 and fives.iloc[-1]["linear regression histogram"] > 0 ):
            print("in five minute candle at... ",fives.iloc[-1]["time"][:2] + ":" + fives.iloc[-1]["time"][2:4] + ":" + fives.iloc[-1]["time"][4:]) 
                             
            if ones.iloc[-1]["linear regression histogram"] > 0:
                print( "    in one minute candle at... ",ones.iloc[-1]["time"][:2] + ":" + ones.iloc[-1]["time"][2:4] + ":" + ones.iloc[-1]["time"][4:]) 
                                     
                if fourths.iloc[-1]["linear regression histogram"] > 0 and fourths.iloc[-2]["linear regression histogram"] < 0:
                    print( "        in fourth minute candle at... ",fourths.iloc[-1]["time"][:2] + ":" + fourths.iloc[-1]["time"][2:4] + ":" + fourths.iloc[-1]["time"][4:]) 
                                             
                    if twelfths.iloc[-1]["linear regression histogram"] > 0 and twelfths.iloc[-2]["linear regression histogram"] < 0:
                        print( "            in twelfth candle at... ",twelfths.iloc[-1]["time"][:2] + ":" + twelfths.iloc[-1]["time"][2:4] + ":" + twelfths.iloc[-1]["time"][4:] ) 
                        print( ">           open/buy at... ",twelfths.iloc[-1]["open"] )
                                          
                        bot.reqIds(-1)
                        order_id = bot.nextValidOrderId
                        bot.placeOrder( order_id,ticker,marketToLimit("BUY",1 ))
                        
                        t.sleep(1)
                        
                        bot.reqIds(-1)
                        order_id = bot.nextValidOrderId
                        bot.placeOrder( order_id,ticker,limitOrder("SELL",1,twelfths.iloc[-1]["open"] ))
                                             
                                         
                '''                     
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
 
                    
                    for a in range(len( ones )):
                        if(( int(ones.iloc[a]["time"]) >  93000 and int(ones.iloc[a]["time"]) < 160000 and
                             int(ones.iloc[a]["time"]) - int(fives.iloc[i]["time"]) <= 400 and int(ones.iloc[a]["time"]) - int(fives.iloc[i]["time"]) >= 0 and 
                             ones.iloc[a]["linear regression histogram"] > 0 )):
                            print("in five minute candle at... ",fives.iloc[i]["time"][:2] + ":" + fives.iloc[i]["time"][2:4] + ":" + fives.iloc[i]["time"][4:]) 
                            print( "    in one minute candle at... ",ones.iloc[a]["time"][:2] + ":" + ones.iloc[a]["time"][2:4] + ":" + ones.iloc[a]["time"][4:]) 
                            
                            for b in range(len( fourths )):
                                if(( int(fourths.iloc[b]["time"]) >  93000 and int(fourths.iloc[b]["time"]) < 160000 and
                                     int( fourths.iloc[b]["time"] ) - int( ones.iloc[a]["time"] ) <= 45 and int( fourths.iloc[b]["time"] ) - int( ones.iloc[a]["time"] ) >=0 and 
                                     fourths.iloc[b]["linear regression histogram"] > 0 and fourths.iloc[b-1]["linear regression histogram"] < 0)): 
                                    print( "        in fourth minute candle at... ",fourths.iloc[b]["time"][:2] + ":" + fourths.iloc[b]["time"][2:4] + ":" + fourths.iloc[b]["time"][4:]) 
                                    
                                    for c in range(len( twelfths )):
                                        if(( int(twelfths.iloc[c]["time"]) >  93000 and int(twelfths.iloc[c]["time"]) < 160000 and
                                             int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) <= 10 and int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) >= 0  and 
                                             twelfths.iloc[c]["linear regression histogram"] > 0 and twelfths.iloc[c-1]["linear regression histogram"] < 0 )):
                                                 
                                                  print( "            *** in twelfth candle buy event at... ",twelfths.iloc[c]["time"][:2] + ":" + twelfths.iloc[c]["time"][2:4] + ":" + twelfths.iloc[c]["time"][4:] ) 
            except Exception as e:
                print( e )    
                
                
                
                def marketToLimit( action,quantity ):
                    order                = Order()
                    order.action         = action
                    order.orderType      = "MTL"
                    order.totalQuantity  = quantity
                    return order
                    
                
                def limitOrder( action,quantity,price ):
                    order               = Order() 
                    order.action        = action 
                    order.orderType     = "LMT"
                    order.totalQuantity = quantity
                    order.lmtPrice      = price
                    return order
                
                
                
                bot.placeOrder( order_id,5, )
                
                bot.placeOrder( order_id+3,ticker,marketToLimit("BUY",1 ))
                
                
                
                
                ticker

                order = Order() 
                order.action = "BUY" 
                order.orderType = "MKT"
                order.totalQuantity = 1
                order.tif = "OPG" 
                order.lmtPrice = 10

                bot.placeOrder( bot.nextValidOrderId+1, ticker, order )
                bot.reqIds(-1)
                time.sleep(2)
                order_id = bot.nextValidOrderId
                bot.placeOrder( order_id, usTechStk("FB"), limitOrder("BUY",5,25 ))
                time.sleep(3)

                app.cancelOrder( order_id )
                
                
                
                def marketOnOpen( action,quantity ):
                    order               = Order() 
                    order.action        = action
                    order.orderType     = "MKT"
                    order.totalQuantity = quantity
                    order.tif           = "OPG"
                    
                
                def limitOrder( action,quantity,price ):
                    order               = Order() 
                    order.action        = action 
                    order.orderType     = "LMT"
                    order.totalQuantity = quantity
                    order.lmtPrice      = price
                    return order
                
                
                
                
                
               order = Order()
    2         order.action = action
    3         order.orderType = "MKT"
    4         order.totalQuantity = quantity
    5         order.tif = "OPG"   
                
                
                
                
                
                
                
# template for limit order 
def limitOrder(direction,quantity,lmt_price):
    order = Order() 
    order.action = direction 
    order.orderType = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice = lmt_price
    return order

# template for market order
def marketOrder(direction,quantity):
    order = Order() 
    order.action = direction 
    order.orderType = "MKT"
    order.totalQuantity = quantity
    return order

def stopOrder(direction,quantity,st_price):
    order = Order() 
    order.action = direction 
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.auxPrice = st_price
    return order

def trailStopOrder(direction,quantity,stp_price,tr_step=1):
    order = Order()
    order.action = direction
    order.orderType = "TRAIL"
    order.totalQuantity = quantity
    order.auxPrice = tr_step
    order.trailStopPrice = stp_price
    return order


                
                
                
                    for a in range(len( ones )):
                        if(( int(ones.iloc[a]["time"]) >  93000 and int(ones.iloc[a]["time"]) < 160000 and
                             int(ones.iloc[a]["time"]) - int(fives.iloc[i]["time"]) < 5 and int(ones.iloc[a]["time"]) - int(fives.iloc[i]["time"]) >= 0 and 
                             ones.iloc[a]["adx"] > 20 and ones.iloc[a]["linear regression histogram"] > 0 and ones.iloc[a-1]["linear regression histogram"] < 0 )):
                            print("in five minute candle at... ",fives.iloc[i]["time"][:2] + ":" + fives.iloc[i]["time"][2:4] + ":" + fives.iloc[i]["time"][4:]) 
                            print( "    in one minute candle at... ",ones.iloc[a]["time"][:2] + ":" + ones.iloc[a]["time"][2:4] + ":" + ones.iloc[a]["time"][4:]) 
                            
                            for b in range(len( fourths )):
                                if(( int(fourths.iloc[b]["time"]) >  93000 and int(fourths.iloc[b]["time"]) < 160000 and
                                     int( fourths.iloc[b]["time"] ) - int( ones.iloc[a]["time"] ) <= 45 and int( fourths.iloc[b]["time"] ) - int( ones.iloc[a]["time"] ) >=0 and 
                                     fourths.iloc[b]["adx"] > 20 and fourths.iloc[b]["linear regression histogram"] > 0 and fourths.iloc[b-1]["linear regression histogram"] < 0 )): 
                                    print( "        in fourth minute candle at... ",fourths.iloc[b]["time"][:2] + ":" + fourths.iloc[b]["time"][2:4] + ":" + fourths.iloc[b]["time"][4:]) 
                                          
                                    for c in range(len( twelfths )):
                                        if(( int(twelfths.iloc[c]["time"]) >  93000 and int(twelfths.iloc[c]["time"]) < 160000 and
                                             int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) <= 10 and int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) >= 0  and 
                                             twelfths.iloc[c]["adx"] > 20 and twelfths.iloc[c]["linear regression histogram"] > 0 and twelfths.iloc[c-1]["linear regression histogram"] < 0 )):
                                             #int(twelfths.iloc[c]["close"]) < int( twelfths.iloc[c]["low band"] )):
                                                 
                                                  print( "            in twelfth candle at buy event at... ",twelfths.iloc[c]["time"][:2] + ":" + twelfths.iloc[c]["time"][2:4] + ":" + twelfths.iloc[c]["time"][4:])   
            except Exception as e:
                print( e )
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    for a in range(len( ones )):
                        if(( int(ones.iloc[a]["time"]) >  93000 and int(ones.iloc[a]["time"]) < 160000 and
                             int(ones.iloc[a]["time"][:4]) - int(fives.iloc[i]["time"][:4]) < 5 and 
                             ones.iloc[a]["adx"] > 20 and ones.iloc[a]["linear regression histogram"] > 0 )):
                            print( ones.iloc[a]["time"] )
                            
                            for b in range(len( fourths )):
                                if(( int(fourths.iloc[b]["time"]) >  93000 and int(fourths.iloc[b]["time"]) < 160000 and
                                     int( fourths.iloc[b]["time"][:4] ) - int( ones.iloc[a]["time"][:4] ) <= 45 and 
                                     fourths.iloc[b]["adx"] > 20 and fourths.iloc[b-1]["linear regression histogram"] > 0)): 
                                    print( fourths.iloc[b]["time"] ) 
                                    
                                    for c in range(len( twelfths )):
                                        if(( int(twelfths.iloc[c]["time"]) >  93000 and int(twelfths.iloc[c]["time"]) < 160000 and
                                             int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) < 5 and 
                                             twelfths.iloc[c]["adx"] > 20 and twelfths.iloc[c]["linear regression histogram"] > 0 )):
                                           
                                            print( "buy event at... ",twelfths.iloc[c]["time"]," ****** " )

            except Exception as e:
                print( e ) 
        
        
        
        
        
        
        
        
bot.reqPositions()

pos_df = bot.pos_df
pos_df.drop_duplicates(inplace=True,ignore_index=True)

bot.reqOpenOrders()

ord_df = bot.order_df

# define quantity

bot.reqIds(-1)

order_id = bot.nextValidOrderId
quantity = 5 

bot.placeOrder(order_id+1,ticker,marketOrder("BUY",quantity))
bot.placeOrder(order_id+1,ticker,stopOrder("SELL",quantity,round(ones["close"][-1]-ones["atr"][-1],1)))


        
        
        
        
        
        
        
        if fives.iloc[-1]["adx"] > 20: 
            if fives.iloc[-1]["linear regression histogram"] > 0:
                if ones.iloc[-1]["adx"] > 20:
                    if ones.iloc[-1]["linear regression histogram"] > 0:
                        if ones.iloc[-2]["linear regression histogram"] > 0:
                            if fourths.iloc[-1]["adx"] < 20:
                                if fourths.iloc[-2]["linear regression histogram"] > 0:
                                    if twelfths.iloc[-1]["adx"] < 20:
                                        if twelfths.iloc[-1]["linear regression histogram"] < 0:
                                            
                                            print( "buy event at... ",dt.datetime.fromtimestamp(time).strftime('%H%M%S') )

       





















i = 94
ii = 469
iii = 1876
iiii =9222


for i in range(len( fives )): 
    try: 
        if( int(fives.iloc[i]["time"]) >  93000 and int(fives.iloc[i]["time"]) < 160000 and
        fives.iloc[i]["adx"] > 20 and fives.iloc[i]["linear regression histogram"] > 0 ):
            print(fives.iloc[i]["time"])
            
            for a in range(len( ones )):
                if(( int(ones.iloc[a]["time"]) >  93000 and int(ones.iloc[a]["time"]) < 160000 and
                     int(ones.iloc[a]["time"][:4]) - int(fives.iloc[i]["time"][:4]) < 5 and 
                     ones.iloc[a]["adx"] > 20 and ones.iloc[a]["linear regression histogram"] > 0 )):
                    print( ones.iloc[a]["time"] )
                    
                    for b in range(len( fourths )):
                        if(( int(fourths.iloc[b]["time"]) >  93000 and int(fourths.iloc[b]["time"]) < 160000 and
                             int( fourths.iloc[b]["time"][:4] ) - int( ones.iloc[a]["time"][:4] ) <= 45 and 
                             fourths.iloc[b]["adx"] < 20 and fourths.iloc[b-1]["linear regression histogram"] > 0)): 
                            print( fourths.iloc[b]["time"], " <<<<<<<< ") 
                            
                            for c in range(len( twelfths )):
                                if(( int(twelfths.iloc[c]["time"]) >  93000 and int(twelfths.iloc[c]["time"]) < 160000 and
                                     int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) < 5 and 
                                     twelfths.iloc[c]["adx"] < 20 and twelfths.iloc[c]["linear regression histogram"] < 0 )):
                                   
                                    print( "buy event at... ",twelfths.iloc[c]["time"] )

    except Exception as e:
        print( e ) 



               
                for a in range(len( ones )):
                    if( int( ones.iloc[a]["time"][:4] ) - int( fives.iloc[i]["time"][:4] ) < 5 and 
                       ones.iloc[a]["adx"] > 20 and ones.iloc[a]["linear regression histogram"] > 0 ):
                        print( fives.iloc[i]["time"] )
                        print( ones.iloc[a]["time"] )
                        
                        for b in range(len( fourths )):
                            if( int( fourths.iloc[b]["time"][:4] ) - int( ones.iloc[a]["time"][:4] ) <= 45 and 
                               fourths.iloc[b]["adx"] < 20 and fourths.iloc[b-1]["linear regression histogram"] > 0) : 
                                print( fourths.iloc[b]["time"] ) 
                                
                                for c in range(len( twelfths )):
                                    if( int( twelfths.iloc[c]["time"] ) - int( fourths.iloc[b]["time"] ) < 5 and 
                                       twelfths.iloc[c]["adx"] < 20 and twelfths.iloc[c]["linear regression histogram"] < 0) :
                                        print( "buy event at... ",twelfths.iloc[c]["time"] )
                                   
    except Exception as e:
        print( e )           
                
                
            if ones.iloc[i]["adx"] > 20:
                if ones.iloc[i]["linear regression histogram"] > 0:
                    if ones.iloc[i-1]["linear regression histogram"] > 0:
                        if fourths.iloc[i]["adx"] < 20:
                            if fourths.iloc[i-1]["linear regression histogram"] > 0:
                                if twelfths.iloc[i]["adx"] < 20:
                                    if twelfths.iloc[i]["linear regression histogram"] < 0:
                                        
                                        print( "buy event at... ",twelfths.iloc[-1]["time"] )
            
        

















             
    if fives.iloc[-1]["adx"] > 20: 
        if fives.iloc[-1]["linear regression histogram"] > 0:
            if ones.iloc[-1]["adx"] > 20:
                if ones.iloc[-1]["linear regression histogram"] > 0:
                    if ones.iloc[-2]["linear regression histogram"] > 0:
                        if fourths.iloc[-1]["adx"] < 20:
                            if fourths.iloc[-2]["linear regression histogram"] > 0:
                                if twelfths.iloc[-1]["adx"] < 20:
                                    if twelfths.iloc[-1]["linear regression histogram"] < 0:
                                        
                                        print( "buy event at... ",dt.datetime.fromtimestamp(time).strftime('%H%M%S') )
            
        
        
    
      
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    pyp.plot(fives['time'],fives[' ln( histogram )'])
    pyp.plot(ones['time'],ones[' ln( histogram )'])
    
    
    
    pyp.plot(fives['time'],fives[' ln( histogram )'],ones[' ln( histogram )'])
    
    
# line 1 points
x1 = [10,20,30]
y1 = [20,40,10]
# plotting the line 1 points 
plt.plot(x1, y1, label = "line 1")
# line 2 points
x2 = [10,20,30]
y2 = [40,10,30]
# plotting the line 2 points 
plt.plot(x2, y2, label = "line 2")
plt.xlabel('x - axis')
# Set the y axis label of the current axis.
plt.ylabel('y - axis')
# Set a title of the current axes.
plt.title('Two or more lines on same plot with suitable legends ')
# show a legend on the plot
plt.legend()
# Display a figure.
plt.show()

    
    
    
    
    
    
    
    
    
    
    
    
    
    '''
    logic

    5 min candles
    adx above 20
    linear regression line last three candles histogram increasing

    1 min candles
    linear regression line last four candles histogram increasing
    adx above 20

    15 second candles 
    linear regression line last four candles histogram increasing
    adx below 20 

    5 sec candles
    adx below 20 
    sell at maximums of adx 
    at close 
    '''
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    if int(bot.newOHLCV['time']) > int(twelfths.iloc[-1]['time']):
    
    
    for twelfth in range(len( twelfths )):
        if int(bot.newOHLCV['time']) > int(twelfths.iloc[-1]['time']):
            twelfths = twelfths.append( bot.newOHLCV,ignore_index=True )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    newCndlTime    = int(bot.newOHLCVlist[-1]['time']) 
    rcntHistTime   = int(twelfths.iloc[-1]['time'])
    gap = newCndlTime - rcntHistTime
    
    if gap==5:
        
    
    if gap > 11 : 
        for i in range(len())
        twelfths = twelfths.append( bot.newOHLCV,ignore_index=True )
    
        
        if(( twelfths.iloc[-3]['time'][4:] == "00" and twelfths.iloc[-2]['time'][4:] == "05" and twelfths.iloc[-1]['time'][4:] == "10" ) or 
           ( twelfths.iloc[-3]['time'][4:] == "15" and twelfths.iloc[-2]['time'][4:] == "20" and twelfths.iloc[-1]['time'][4:] == "25" ) or 
           ( twelfths.iloc[-3]['time'][4:] == "30" and twelfths.iloc[-2]['time'][4:] == "35" and twelfths.iloc[-1]['time'][4:] == "40" ) or 
           ( twelfths.iloc[-3]['time'][4:] == "45" and twelfths.iloc[-2]['time'][4:] == "50" and twelfths.iloc[-1]['time'][4:] == "55" )) :
            
            newFourth = [{ 'time'  : twelfths.iloc[-3]['time'],
                           'open'  : twelfths.iloc[-3]["open"],
                           'high'  : max( twelfths[-3:-1]["high"] ), 
                           "low"   : min( twelfths[-3:-1]["low"] ),
                           "close" : twelfths.iloc[-1]['close'],
                           "volume": sum( twelfths[-3:-1]["volume"] )  }]
            
            fourths = fourths.append( newFourth,ignore_index=True )
            
            if twelfths.iloc[-1]['time'][4:] == "55" and ones.iloc[-12]['time'][4:] == "00":
                
                newOne = [{ "time"  : fourths.iloc[-12]['time'],
                            "open"  : fourths.iloc[-12["open"],
                            "high"  : max(fourths[-12:-1]["high"]), 
                            "low"   : min(fourths[-12:-1]["low"]),
                            "close" : fourths.iloc[-1]['close'],
                            "volume": sum(fourths[-12:-1]["volume"]) }]
                
                ones = ones.append( newOne,ignor_index=True )
                
                if twelfths.iloc[-60]["time"][4:] == "00": 
                    
                    newFive = 
                    
                    
                    fives = fives.append( newFive,ignore_index.=True )
            
            
            
            
            
            
            
            
            def makeFourths( twelfthsDF ): 
                fourths = pd.DataFrame()
                i = 0
                for twelfth in range(len( twelfths )):
                    try:
                        if(( twelfths.at[twelfth-2,'time'][4:] == "00" and twelfths.at[twelfth-1,'time'][4:] == "05" and twelfths.at[twelfth,'time'][4:] == "10" ) or 
                           ( twelfths.at[twelfth-2,'time'][4:] == "15" and twelfths.at[twelfth-1,'time'][4:] == "20" and twelfths.at[twelfth,'time'][4:] == "25" ) or 
                           ( twelfths.at[twelfth-2,'time'][4:] == "30" and twelfths.at[twelfth-1,'time'][4:] == "35" and twelfths.at[twelfth,'time'][4:] == "40" ) or 
                           ( twelfths.at[twelfth-2,'time'][4:] == "45" and twelfths.at[twelfth-1,'time'][4:] == "50" and twelfths.at[twelfth,'time'][4:] == "55" )) :
                            
                            t  = twelfths.at[twelfth-2,'time']
                            o  = twelfths.at[twelfth-2,'open']
                            h  = max( twelfths[twelfth-2:twelfth]['high'] )
                            l  = min( twelfths[twelfth-2:twelfth]['low'] )
                            c  = twelfths.at[twelfth,'close']
                            v  = sum( twelfths[twelfth-2:twelfth]['volume'] )
                            cndl    = [{ 'time':t,'open':o,'high':h,'low':l,'close':c,'volume':v }]
                            fourths = fourths.append( cndl,ignore_index=True )
                            i +=1
                    except Exception as e : print(e) 
                return fourths


            
            
            
            
            
            
            
            fourths = fourths.append(  )
           
            if fourths.iloc[-1]['time'][4:] == "00" and fourths.iloc[-5]['time'][4:] == ""
        
        
        
        
        if stackTwelfths:
            fourths = 
    
    
    
    
    
    print('running... ')
    t.sleep(1)



  if aggregate(4) : 
      fourths = fourths.append( stack(-3,-1,twelfths ))
      if aggregate(12) : 
          ones = ones.append( stack(-12,-1,twelfths  ))
          if aggregate(60) : 
              fives = fives.append( stack(-60,-1,twelfths ))













for interval in range( 0,len(stream )):
    for study in range( len(studies )):
        stream[interval] = studies[study]( stream[interval] )
    
 


# STACK 5sec BARS ON HISTORICAL BAR DATAFRAME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Now              = int(dt.datetime.now().strftime("%H%M%S"))
marketClose      = 160000

while Now < marketClose :
    for interval in range( 0,len(stream )):
        for new5bar in bot.newOHLCVlist:
            if new5bar['time'] > stream[interval].iloc[-1]['time']:
                stream[interval] = stream[interval].append( new5bar,ignore_index=True )
                for study in range( len(studies )):
                    stream[interval] = studies[study]( stream[interval] )
                    
  while Now < marketClose :
          for new5bar in bot.newOHLCVlist:
              if new5bar['time'] > ones.iloc[-1]['time']:
                  ones = ones.append( new5bar,ignore_index=True )
                  for study in range( len(studies )):
                      stream[interval] = studies[study]( ones )
                      
subscription = bot.newOHLCVlist                                   
while Now < marketClose : 
    for newTwelth in range(len( subscription )) :
        if newTwelth['time'] > twelths.iloc[-1]['time'] :
            if newTwelth=
            twelths = twelths.append( newTwelth,ignore_index=True )
            # append studies
            if 
        
                    
         
            
         
            
                    

                    
                    
                    if makeOne:  buildCandle( stream[interval],1 ) 
                    if makeFive: buildCandle( stream[interval],5 ) 
                    
                    bDF =  stream[0] bDF.drop( bDF.index[len(bDF)-1] )
                    
                    
                    
'''
logic

5 min candles
adx above 20
linear regression line last three candles histogram increasing

1 min candles
linear regression line last four candles histogram increasing
adx above 20

15 second candles 
linear regression line last four candles histogram increasing
adx below 20 

5 sec candles
adx below 20 
sell at maximums of adx 
at close 
'''
                    
def buildCandle( bDF,size ):  
    if size==1: size = 12 
    if size==5: size = 12*5
    stack = bDF[-size:len(bDF.index)].copy()
    
     
    time   = stack.iloc[-1]['time']
    open_  = stack.iloc[-size]['open']
    high   = max( stack['high'] )
    low    = min( stack['low']  ) 
    close  = stack.iloc[-1]['close']
    
    minStack = [ {"time":time,"open":open_,"high":high,"low":low,"close":close}  ]
    
    bDF = bDF.drop( bDF.index[len(bDF) - size:len(bDF)] ) 
    
    bDF = bDF.append( minStack )
    
    
    
    
    
    
    
    
    
    
    
    
    
    for column in bDF.columns: 
        bDF.iloc[-1][column] = 0 
    
    
    
    
    
    
    bDF.iloc[-size:-1]
    
    
    
    
    
    
    
    
    
    barsRequired
    
    bDF = bDF.drop( bDF.index[len(bDF)-1]  ) 
    
    
    for column in range(len( bDF.columns )):
        
                
                
            makeOne  = [   streamnterval].iloc[-12]['time'][-2:]=="00"   and    stream[interval].iloc[-1]['time'][-2:]=="00"   ] 
            makeFive = [   stream[interval].iloc[-1]['time'][-2:]=="00"    and    int(stream[interval].iloc[-1]['time'][-2:])-int(stream[interval].iloc[-1]['time'][-2:])==5   ]
            if 
            



stream














while Now < marketClose :
    for candle in bot.newOHLCVlist: 
        for interval in range(0,len(stream)):
            if float(candle['t'])  >  float(stream[interval].iloc[-2]['time']):     
                stream[interval] = stream[interval].append( candle,ignore_index=True )   
                for study in range(len(studies)):
                    stream[interval] = studies[study]( stream[interval] )





for interval in range(0,len( stream )):
    for new5bar in bot.newOHLCVlist:
        if new5bar['time'] > stream[interval].iloc[-1]['time']:
            stream[interval] = stream[interval].append( new5bar,ignore_index=True )
            for study in range(len( studies )):
                stream[interval] = studies[study]( stream[interval] )
            
    
    for  in bot.newOHLCVlist: 
        if float(cndl['time'])  >  float(fives.iloc[-1]['time']): 
            efives = fives.append( cndl,ignore_index=True ) 
            
            for intrvl in range(len(stream)):
            
            
            for study in range(len(studies)):
                ones = studies[study]( ones )    
        
        stream[0]
        
        
        stream[interval-1] = stream[interval-1].append( cndl,ignore_index=True )  
                     
                    
                
                
                for candle in bot.newOHLCVlist: 
                    for interval in range(0,len(stream)):
                stream[interval] = stream[interval].append( candle,ignore_index=True )   
                for study in range(len(studies)):
                    stream[interval] = studies[study]( stream[interval] )        
        
        
        
        
        
        
        
        
        
        
        
        

Now              = int(dt.datetime.now().strftime("%H%M%S"))
marketClose      = 160000
while Now < marketClose :



    
# CREATE HISTORICAL BAR DATAFRAME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def makeMinuteBars( candles,minLength=1,newCandle=None, ):
          if newCandle:
              candles = candles.append( newCandle,ignore_index=True)
              barsInMin = 12 
              z = barsInMin * minLength 
              lastBarClose = int((candles.index[-1]//z)*z)
              fromLastClose = int(candles.index[-1] - lastBarClose)
              candles.at[len(df)-1,'minute low'] = min( candles[ lastBarClose : lastBarClose + fromLastClose ]['l'])
          else:
              candles['MIN'] = candles['t'].str[8:-2]
              candles['minute low'] = 0
              candles = candles.drop([0,1,2,3,4,5,6])         
              candles.index = np.arange( 0,len(candles) )  
              for i in range(0,candles.index[-1],12):
                  for ii in range(0,12):
                      if i!=i+ii:
                          candles.at[i+ii,'minute low']  = min( candles[i:i+ii]['l'] )
                          candles.at[i+ii,'minute high'] = max( candles[i:i+ii]['h'] )
                          candles.at[i+ii,'minute open'] = candles.at[i+1,'o']   
                          candles.at[i+ii,'minute close'] = candles.at[ii,'c']                        
                      else: 
                          candles.at[i,'minute low'] = candles.at[i,'l']
          return candles


    if int( bot.liveBarReceived['t'] ) > int( bars.iloc[-1]['t'] ) :
        bars = bars.append( bot.liveBarReceived,ignore_index=True)
        bars = macd( bars,True )
        bars = atr( bars,True )
        bars = ema( bars,True )
        bars = keltchan( bars,True )
        
    else :
        
        i = bars.index.stop-1
        momentumLull = 0 
        minEntryChange = 0 
        
        
        
    for i in range(len(bars)): 
        
        
        if (bars.at[i,'histogram'] < momentumLull and 
        bars.at[i,'hist Slope'] > minEntryChange and
        bars.at[i-1,'hist Slope'] > minEntryChange and
        bars.at[i-2,'hist Slope'] > minEntryChange and 
        bars.at[i,'c'] > bars.at[i,'low band'] and 
        bars.at[i-1,'c'] < bars.at[i-1,'low band'] ):
            bars.at[i,'buy on next open'] = True
                               
            order_id             = bot.nextValidOrderId
            order                = Order()
            order.action         = "BUY" 
            order.tif            = "OPG"
            order.orderType      = "LMT"
            order.totalQuantity  = 10
            order.lmtPrice       = bot.liveBarReceived['c']
                   
        else: bars.at[i,'buy on next open'] = False

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
for candle in bot.newOHLCVlist:          
               
    if int(candle['time'])  >  int(ones.at[ones.index[-1],'time']):     
        ones = ones.append( candle,ignore_index=True )
        studyNewCandle=True
        
    elif int(candle['time'])  >  int(fives.at[fives.index[-1],'time']):     
        fives = fives.append( candle,ignore_index=True ) 
        studyNewCandle=True
     
    elif studyNewCandle:
        ones   = macd( bars )
        ones   = atr( bars )                                    # applying indicators 
        ones   = ema( bars )
        ones   = keltchan( bars ) 

    else: pass









ones.at[0,'time']


#historyStudies   = [ macdSignalHistogram,atr,stoch ]                          
#liveStudies      = [ macdBar ]


# CREATE HISTORICAL BAR DATAFRAME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

bars = pd.DataFrame( bot.histOHLCV[0] )    
oneMinBars    = makeMinuteBars( pd.DataFrame( bot.hist[0]   ))
fiveMinBars   = makeMinuteBars( pd.DataFrame( bot.hist[0]),5 )


for bar in bot.allLiveBars:                         
    if int( bar['t'] ) > int( bars.iloc[-1]['t']):      # closing gap between historical 
        bars = bars.append( bar,ignore_index=True )     # data load time and incoming bar
        
bars   = macd( bars )
bars   = atr( bars )                                    # applying indicators 
bars   = ema( bars )
bars   = keltchan( bars ) 

Now              = int(dt.datetime.now().strftime("%H%M%S"))
marketClose      = 160000
while Now < marketClose :



    
# CREATE HISTORICAL BAR DATAFRAME >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>



    if int( bot.liveBarReceived['t'] ) > int( bars.iloc[-1]['t'] ) :
        bars = bars.append( bot.liveBarReceived,ignore_index=True)
        bars = macd( bars,True )
        bars = atr( bars,True )
        bars = ema( bars,True )
        bars = keltchan( bars,True )
        
    else :
        
        i = bars.index.stop-1
        momentumLull = 0 
        minEntryChange = 0 
        
        
        
    for i in range(len(bars)): 
        
        
        if (bars.at[i,'histogram'] < momentumLull and 
        bars.at[i,'hist Slope'] > minEntryChange and
        bars.at[i-1,'hist Slope'] > minEntryChange and
        bars.at[i-2,'hist Slope'] > minEntryChange and 
        bars.at[i,'c'] > bars.at[i,'low band'] and 
        bars.at[i-1,'c'] < bars.at[i-1,'low band'] ):
            bars.at[i,'buy on next open'] = True
                               
            order_id             = bot.nextValidOrderId
            order                = Order()
            order.action         = "BUY" 
            order.tif            = "OPG"
            order.orderType      = "LMT"
            order.totalQuantity  = 10
            order.lmtPrice       = bot.liveBarReceived['c']
                   
        else: bars.at[i,'buy on next open'] = False







for i in range(len(bars)): 
    if bars.at[i,'buy on next open'] == True:
        print(bars.iloc[i]['t'],bars.iloc[i+2]['h']-bars.iloc[i+1]['o'])









for i in range(len(bars)-11):
    bars.at[i,'next x bar gain'] = bars.at[i+2,'ema'] - bars.at[i,'ema']
    print( i )
    
for i in range(1,len(bars)):
    bars.at[i,'hist Slope'] = bars.at[i,'histogram'] - bars.at[i-1,'histogram']


pyp.scatter(bars['next x bar gain'],bars['hist Slope'] )
plot.xlabel('next x bar gain')
plot.ylabel('slope of macd hist')

            
        
                
            
            
            
            
            
            
            
            
            
            
            
        
       for i in range(4,len(bars)): 
           if ((  bars.at[i,'histogram'] - bars.at[i-1,'histogram']    ) > 0 and 
               (  bars.at[i-1,'histogram'] - bars.at[i-2,'histogram']  ) > 0 and               
               (  bars.at[i-2,'histogram'] - bars.at[i-3,'histogram']  ) > 0 ):









        # logic 
        
        order_id             = bot.nextValidOrderId
        order                = Order()
        order.action         = "BUY"
        order.orderType      = "LOC"
        order.totalQuantity  = 10
        order.lmtPrice       = float(bars.iloc[-1]['c'])

        if ((bars.iloc[-1]['macd'] - bars.iloc[-2]['macd']) > 0 and 
            (bars.iloc[-2]['macd'] - bars.iloc[-3]['macd']) > 0 and                 # positive slope of last three bars 
            (bars.iloc[-3]['macd'] - bars.iloc[-4]['macd']) > 0):
            
            bot.placeOrder( order_id,tkr,order  )
            
            print(bars.iloc[-1]['macd'],">",bars.iloc[-2]['macd'],">",bars.iloc[-3]['macd'])
                
            
            
            
            
            
        
for i in range(4, len(bars)) : 
    if ((  bars.at[i,'histogram'] - bars.at[i-1,'histogram']    ) > 0 and 
        (  bars.at[i-1,'histogram'] - bars.at[i-2,'histogram']  ) > 0 and               
        (  bars.at[i-2,'histogram'] - bars.at[i-3,'histogram']  ) > 0 ):
      
        bars.at[i,"buy event"] = True
        print(bars.at[i,'histogram'],">",bars.at[i-1,'histogram'],">",bars.at[i-2,'histogram'],bars.at[i-3,'histogram'])
      
        
      
        

      
        
      
        
      
        
      
'''
def macd( bar_df,a=48,b=104,c=36 ):
    df = bar_df.copy()
    df['fast_ma']   = df['c'].ewm( span=a,min_periods=a ).mean()
    df['slow_ma']   = df['c'].ewm( span=b,min_periods=b ).mean()
    df['macd']      = df['fast_ma']-df['slow_ma']
    df['signal']    = df['macd'].ewm( span=c,min_periods=c ).mean()
    # df.dropna( inplace=True )
    return df  
'''

def atr( bar_df,n=60 ):
    df = bar_df.copy()
    df['h-l']      = abs(df['h']-df['l'])
    df['h-pc']     = abs(df['h']-df['c'].shift(1))
    df['l-pc']     = abs(df['l']-df['c'].shift(1))
    df['tr']       = df[['h-l','h-pc','l-pc']].max(axis=1,skipna=False)
    df['atr']      = df['tr'].ewm(com=n,min_periods=n).mean()
    return df 

def stoch( bar_df,a=20,b=3 ):
    df = bar_df.copy()
    df['c-l'] = df['c'] - df['l'].rolling(a).min()
    df['h-l'] = df['h'].rolling(a).max() - df['l'].rolling(a).min()
    df['%k'] = df['c-l']/df['h-l']*100
    #df['%D'] = df['%K'].ewm(span=b,min_periods=b).mean()
    df['%k'].rolling(b).mean()
    return df  
    
def macdBar( df,a=48,bb=104,c=36 ):
    df.loc[df.index[-1],'fast_ma']  = df['c'].ewm( span=a,min_periods=a ).mean().iloc[-1]
    df.loc[df.index[-1],'slow_ma']  = df['c'].ewm( span=bb,min_periods=bb ).mean().iloc[-1]
    df.loc[df.index[-1],'macd']     = df['fast_ma'].iloc[-1]-df['slow_ma'].iloc[-1]
    df.loc[df.index[-1],'signal']   = df['macd'].ewm( span=c,min_periods=c ).mean().iloc[-1]
    return df

def studyLiveBar( df,bar_studies ):
    for s in range(len(bar_studies)):
        df = bar_studies[s]( df )
    return df
        
      
        
      
        
      
        
      
        
        
      
        
      else: bars.at[i,"buy event"] = False
      
      
      
      
      
      
      
      
      

        buyEvents = pd.DataFrame( [{"buy event":False}] )
        bars = bars.append(buyEvents)

bars = bars.append( [pd.DataFrame([i], columns=['buy event']) for i in range(len(bars))],ignore_index=True )











     
maccd,signal,histo = macdd(bars['c'])


macdd()










        x = []
        y = []
        
        for i in range(len(bars)):
            x.append( bars.iloc[-i]['macd'] )
            y.append( int(bars.iloc[-i+2]['h'])  - int(bars.iloc[-i]['c']) )
            
            
            
          for i in range(len(bars)):
              x.append( bars.iloc[-i]['macd'] )
              y.append( float(bars.iloc[-i+1]['h'])  - float(bars.iloc[-i]['c']) )
               
              
              
        for i in range(len(bars)):
            if (bars.iloc[-i+1]['macd'] - bars.iloc[-i]['macd']) > 0 and (bars.iloc[-i+2]['macd'] - bars.iloc[-i+1]['macd']) > 0 and (bars.iloc[-i+3]['macd'] - bars.iloc[-i+2]['macd']) > 0  :
                if bars.iloc[-i+1]['macd'] - bars.iloc[-i]['macd'] > 0.005: # and bars.iloc[-1]['v'] > 10:
                    
                    x.append( bars.iloc[-i+1]['macd'] - bars.iloc[-i]['macd'] )
                    y.append( float(bars.iloc[-i+1]['c'])  - float(bars.iloc[-i]['o']) )
                    
            
        plot.scatter( x,y ) 
        plot.xlabel('macd slope')
        plot.ylabel('positive range of subsequent bars')
        
        avgPosMacd = float(0) 
        for i in range(len(x)):
            avgPosMacd = x[i] + avgPosMacd
        avgPosMacd/len(x)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        x = [] 
        y = 
        
        plot.plot(macdXgain[i])
        macdXgain[0]
        
        bars.iloc[-1]['macd']
        
        
        float(bars.iloc[-1]['c']) - float(bars.iloc[-2]['c'])
        
        
        
        
        
        
        
        for i in range(1,3):
            macdSlope += (bars.iloc[-i]['macd'] - bars.iloc[-i-1]['macd'])
        if macdSlope > minSlope:
            print ("ps slope")
            
                
        # *** identify context trend 
        macdSlope = 0
        
        for i in range(1,3):
            macdSlope += (bars.iloc[-i]['macd'] - bars.iloc[-i-1]['macd'])
        if macdSlope > minSlope:
            print ("ps slope")
            
                    
        for which macd slope average of 3-7 bars is there the greatest increase in close price :
            for logged_slope in macdSlopes:
    
            
        




































if Now > Fin :
    pass
else : On = True

while On:


bars     = pd.DataFrame( bot.hist[0] )          #      <------------ must be done manually
liveBar = bot.liveBarReceived











lastBarReceivedTime = int(bot.hist[0][-1]['t'])
newBarReceivedTime = bot.liveBarReceived['t']

if lastBarReceivedTime < newBarReceivedTime:

    freshBar = bot.liveBarReceived
    for study in range(len( historyStudies )):                 
        bars = historyStudies[study]( bars ) 
    bars = bars.append( freshBar,ignore_index=False )
    lastBarReceived = 
    
    
    
    
    
    bars = studyLiveBar( bars,liveStudies )




Now = int(dt.datetime.now().strftime("%H%M%S"))

while int(bot.hist[0][-1]) <= bot.barReceived['t']:
    print(" yes ")
    break
    
    
    
    
    
bars = pd.DataFrame( bot.hist[0] )                           
for study in range(len( historyStudies )):                 
    bars = historyStudies[study]( bars ) 
print("\n\nhistorical data frame created... ",dt.datetime.now().strftime("%H:%M:%S"))
    
On = False
Now = int(dt.datetime.now().strftime("%H%M%S"))
Fin = 160000

if Now > Fin :
    pass
else : On = True

while On:
    print("\n\nrecieving new bars... ",dt.datetime.now().strftime("%H:%M:%S"))
    freshBar = bot.barReceived
    if freshBar['t'] > int( bars.iloc[-1]['t'] ):
        bars = bars.append( freshBar,ignore_index=False )
        bars = studyLiveBar( bars,liveStudies )
        
    
# *** identify context trend 
macdSlope = 0

for i in range(1,3):
    macdSlope += (bars.iloc[-i]['macd'] - bars.iloc[-i-1]['macd'])
if macdSlope > minSlope:
    print ("ps slope")
    
            
for which macd slope average of 3-7 bars is there the greatest increase in close price :
    for logged_slope in macdSlopes:
    
            

i = 1


plot.plot((bars['macd'])) 
bars['macd']



while t.time() <= fin:
    freshBar = bot.newbar
    if len( freshBar ) != 0:
        if freshBar['t'] > b.iloc[-1]['t']:
            bars = bars.append( freshBar,ignore_index=True )
            bars = studyLiveBar( bars,liveStudies )
            

            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        b.loc[b.index[-1],'fast_ma'] = b['c'].ewm( span=a,min_periods=a ).mean().iloc[-2]
        
        b['c'].ewm( span=a,min_periods=a ).mean() 
        
        b['c'].ewm( span )
        
        b.iloc[-1]
            
        b.at[-1,-1]['fast_ma'] = 2
        b['c'].ewm( span=a,min_periods=a ).mean() 
            
            
            
"""
make historical data dataframe
append studies to each row
append new bar ohlcv to historical data
calculate indicators 


"""            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            df = b 
            
new1 = bot.newbar
            
def macd_one_bar( new, df, a=12,b=26,c=9 ):
    new1['fma']   = b['c'].ewm( span=a,min_periods=a ).mean()
    sma   = b['c'].ewm( span=26,min_periods=26 ).mean()
    macd  = fma-sma
    sig   = df['macd'].ewm( span=c,min_periods=c ).mean()
    return new






    #df = df.append( new,ignore_index=True )
    #return df        

new1 = macd_one_bar( new1, b )




b['c']


            
            for s in range( len(studies) ):                    #   for each studies named in studies list 
                b = studies[s]( b ) 
                

   
if b.iloc[-1]['macd']<=0:        #and b.iloc[-2]['macd']>=0 :
    if pos == 1:
        
        print(" buy event ")
        pos += 1
    
    
    order = Order() 
    order.action = "BUY" 
    order.orderType = "LMT"
    order.totalQuantity = 1
    order.lmtPrice = 10.50
        
    bot.placeOrder(bot.nextValidIdOrderId, stk(tkr), order)  
        
   
    
   
    
   
    
   
    
   
    
   
    
   
    if b.iloc[-1]['macd'] - b.iloc[-2]['macd']:
        print("sig")
    
       
   
    
order = Order() 
order.action = "BUY" 
order.orderType = "LMT"
order.totalQuantity = 1
order.lmtPrice = 10.77

t.sleep(2)
bot.placeOrder(bot.nextValidIdOrderId, stk(tkr), order)  
    
   
    
   
    b = [] 
    for i in range(10):
        bdi = dict( bdf.iloc[i] )
        b.append( bdi )
        
    if b[-1]['macd']
        
        
        
        

    
    
    b[-1]['t']
    
    
    
    
    
    
    
    
    
    
    
    def make_bar( data_stream ):
        bar = {}
        bar['t']  = data_stream["time"]
        bar['o']  = data_stream["open"]
        bar['h']  = data_stream["high"]
        bar['l']  = data_stream["low"]
        bar['c']  = data_stream["close"]
        bar['v']  = data_stream["volume"]
        return bar 

    def make_df( bar_list ):
        new = pd.DataFrame( bar_list,columns=['t','o','h','l','c','v'] )
        new.set_index( 't',inplace=True )
        return new
    
    
    
    def make_bars_list( bars_dataframe ):
        bars = []
        for index,row in b.iterrows():
            bar = {}
            bar['o'] = row['o']
            bar['h'] = row['h']
            bar['l'] = row['l']
            bar['c'] = row['c']
            bar['v'] = row['v']
            bar['macd'] = row['macd']
            bars.append(bar)
            
    
    

for i in range(10):
    
    
    
    
    bd = [dict(b.iloc[-1])]
    bars = [bd]
    bars = bars.append(bd)

type(dict(b.iloc[-1]))






while currenttime > b.iloc[-1]['t'][10:18].replace(':',''):
    
while bot.newbar[0]['t'][10:].replace(':','')     > 
    
while 
    
    c = bot.newbar
    
    c = bot.newbar    
    b = b.append( c )
    
    for s in range(len(studies)): 
        for column in  b.iloc[-1]
            if str(s) == b.iloc[-1]column]:
               b.iloc[-1][column] = studies[s](b.iloc[-1][column])

    c.iloc[0]

c = []
c = bot.newbar
c = [{ 't':00,'o':000,'l':000,'h':00,'c':000,'v':000 }]




tt = dt.datetime.now()

                                    #   ask for market steam of specified equity  
tt.strftime("%H%M%S")
tt = tt.replace(':')
if dt.datetime.now() > b.iloc[-1]['t']

fin = t.time() + 50
while t.time() <= fin:

    b = pd.DataFrame( bot.hist[0] )
    
    
    
    
    
    .merge()
    c = pd.DataFrame(  )
    z = pd.merge( b, )
    
    b.set_index( 't',inplace=True )
    for s in range(len(studies)):                              #   for each studies named in studies list 
        b = studies[s]( b )                                    #   add that study to bars dataframe
    
    
    # add indicators... 
    
    
    
    # convert dataframe to list ?

currenttime = dt.datetime.now()
currenttime = currenttime.strftime("%H%M%S")




    
    bars[-1]['macd']
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    x = pd.DataF
    
    
    
    
    
    
    b.append(bot.ohlcv,ignore_index=True)
    
    
    
    bot.ohlcv
    
    
    
    
    b.append( bot.ohlcv,ignore_index=True )
    b.set_index( 't',inplace=True )
    for s in range(len(studies)):                              #   for each studies named in studies list 
        b = studies[s]( b )                                #   add that study to bars dataframe
          
    
x = make_bar( bot.ohlcv )
b.append(x,ignore_index=True)
                                   #   append each past bar dictionary to list of bars


b[-1]['t'] = bot.ohlcv['t']


b['t'][0]




    b = []                                                     #   bars list of bar dictionaries
    histData( 0,stk("AMC"),'1 D','5 secs'  )                   #   client asks for historical market data
    for i in range(len(bot.hist[0])):
        b.append( bot.hist[0][i] )                             #   append each past bar dictionary to list of bars
    
    if bot.ohlcv["time"] != b[-1]['t']:
        b.append( make_bar( bot.ohlcv ),ignore_index=True )                      #   make each bar, include it in list of bars 
        bdf = make_df( b )                                     #   using list of bars convert to dataframe

    for s in range(len(studies)):                              #   for each studies named in studies list 
        bdf = studies[s]( bdf )                                #   add that study to bars dataframe
        b[-1][str(s)] = bdf[str(s)].iloc[-1]                   #   then add it to the bars list
            
            
            

        bdf = atr( bdf )
        bdf = stoch( bdf )


# ^ should make dataframe first ... then convert to bar list 



# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
bdf['macd'][2]
    
    
    
    m
    
    
    
b.append(bar)
    
    
    
    
    
    
    
    
    
    
    

        
        
        
        
        
       ohlcv_data['t'] = bar_list['t'][-i]
       ohlcv_data['o'] = bar_list['o'][-i]
       ohlcv_data['h'] = bar_list['h'][-i]
       ohlcv_data['l'] = bar_list['l'][-i]
       ohlcv_data['c'] = bar_list['c'][-i]
       ohlcv_data['v'] = bar_list['v'][-i]



def macd( bars_list,a=12,b=26,c=9 ):
    ohlcv_data = pd.DataFrame( columns=['t','o','h','l','c','v'] )
    for i in range(len(bar_list)):
       ohlcv_data['t'] = bar_list['t'][-i]
       ohlcv_data['o'] = bar_list['o'][-i]
       ohlcv_data['h'] = bar_list['h'][-i]
       ohlcv_data['l'] = bar_list['l'][-i]
       ohlcv_data['c'] = bar_list['c'][-i]
       ohlcv_data['v'] = bar_list['v'][-i]
       


b = macd( b )








def make_indicators( bar_ ):
    bar = macd( bar )
    bar = rsi( bar )
    bar = stoch( bar )
    bar = keltner( bar )
    bar = adx( bar )
    return bar 
    

    
    
def macd( bars,a=12,b=26,c=9 ):
   for i in range(len(bars)):
       
    
   
    bar_.['c'][-1]
    
    
    macd_df = pd.DataFrame( columns=["close"] )

    


def MACD(DF,a=12,b=26,c=9):
    df = DF.copy()
    df['MA_Fast'] = df['Close'].ewm(span=a,min_periods=a).mean()
    df['MA_Slow'] = df['Close'].ewm(span=b,min_periods=b).mean()
    df['MACD'] = df['MA_Fast']-df['MA_Slow']
    df['Signal'] = df['MACD'].ewm(span=c,min_periods=c).mean()
    df.dropna(inplace=True)
    return df
    
    
    
    bars["macd"]
    br["rsi"]
    br["adx"]
    br["k_up"]
    br["k_low"]
    br["stoch"]

    bar['macd'] = stream["vwap"]
    bar['rsi'] = stream["vwap"]
    bar['adx'] = stream["vwap"]
    bar['k_up'] = stream["vwap"]
    bar['k_low'] = stream["vwap"]
    bar['stoch'] = stream["vwap"]
    bar['ema'] = stream["vwap"]

b = []
fin = t.time() + 50
while t.time() <= fin:
    if bot.ohlcv["time"] != b[-1]['t']:
        b.append( make_bar( bot.ohlcv ) )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
if b[-1]['c'] > b[-2]['c']:
        print("rising")









print(b)

print(bot.ohlcv["time"])
print( b[-1]['c'] > b[-2]['c'] )


bot.ohlcv["time"] in b 
























start = t.time()
fin = t.time() + 15 #60*60*3


def main():
    fin = t.time() + 15
    b = []
    while t.time() <= fin:
        if bot.ohlcv["time"] not in b:
            b.append( make_bars(bot.ohlcv) )

b
main() 

print(b)

bot.ohlcv["reqId"] not in b

OOO = bot.bars
 
print(OOO)








bot.ohlcv





















b[-1]['o'] > b[-2]['o']


b.append( bot.ohlcv["open"] )
print(b)
t.sleep(1)

print(bot.O)


x = bot.bars



b.append()







b = []
b.append( bot.ohlcv )
b
    
print("bbbbbb---->",b,"<<<<<")
    
    















class bar( mkd ):
    def __init__( self ):
        self.t = ohlcv["time"]
        self.o = ohlcv["open"]
        self.l = ohlcv["low"]
        self.h = ohlcv["high"]
        self.c = ohlcv["close"]
        self.v = ohlcv["volume"]
        
    
        
b = bot.ohlcv["time"]    
    
    
b = {{[]}}

start = t.time()
fin = t.time() + 10 #60*60*3

while t.time() <= fin:
    new = bar()
    b.append( new )      
        
        
b = [ {3:"ee"} ]
        
        
b[-1]['o']
        
        
def bars( ohlcv ):
    b = {}
    b[t] = {}
    b[t][o] = ohlcv["open"]
    
        
        
        
b{ time:b, time:b, time:b }    
        
        
b = []

b[-1][]
        
        
b = [ {"time":00,'o':3,'h':1,'l':2,'c':3,'v':4},{"time":00,'o':0,'h':1,'l':2,'c':3,'v':4},{"time":00,'o':123,'h':1,'l':2,'c':3,'v':4} ]       
b[-1]['o'] > b[0]['o']
        
        
        
        
        
        
b0 = bar()
b1 = bar()
b2 = bar() 

b = [b0,b1,b2]

b[-1].t

if bar[-1].open > 

bar = { "time":   {"open":1,"high":2,"low":3,"close":4,"volume":5} }
bar1 = { "time1":   {"open":11,"high":22,"low":33,"close":44,"volume":55} }
bar2 = { "time2":000,"open":111,"high":222,"low":333,"close":444,"volume":555} }



br = [ bar,bar1,bar2 ] 

br[-1]["time2"]

bar[-1]

def make_bar( bot_ ):
    new_bar = { "time":bot_.time,
                 "open":bot_.open,
                 "high":bot_.high,
                 "low":bot_.low,
                 "close":bot_.close,
                 "volume":bot_.volume }
    return new_bar




bot_ = bot() 
d= bot_.ohlcv

ti  =bot.ohlcv["time"]


ti  = bars[-1]["time"]
op  = bars[-1]["open"]
lo  = bars[-1]["high"]
hi  = bars[-1]["low"]
cl  = bars[-1]["close"]
vo  = bars[-1]["volume"]




































def recieve_bar( bot_ ):
    new_bar = { "time":bot_.time,
                 "open":bot_.open,
                 "high":bot_.high,
                 "low":bot_.low,
                 "close":bot_.close,
                 "volume":bot_.volume }
    return new_bar



bars = [{"time":0,"open":1,"high":2,"low":3,"close":4,"volume":5},{"time":00,"open":11,"high":22,"low":33,"close":44,"volume":55}]


ti  = bars[-1]["time"]
op  = bars[-1]["open"]
lo  = bars[-1]["high"]
hi  = bars[-1]["low"]
cl  = bars[-1]["close"]
vo  = bars[-1]["volume"]


print(ti)







def make1MinuteBars( barDataFrame,liveBar=False ):
    df = bars.copy()
    #df.drop(df.index[:1], inplace=True)
    if liveBar==False:
        df['MIN'] = df['t'].str[8:-2]    
        df = df.drop([0,1,2,3,4,5,6])         
        df.index = np.arange( 1,len(df)+1 )  
        #df['minute low'] = 0
        for i in range(0,df.index[-1]):
            print(i)
            lowestLow = 0 
            highestHigh = 0
            start = ((df.index[i]//12)*12)
            end = start+11
            if start<0 or end<12:
                lowestLow = min( df[0:12]['l'] )
            else:
                lowestLow = min( df[start:end]['l'] )
            df.at[i+2,'minute low'] = float(lowestLow)
            
            
            
            
            
            
            
            
            
            
            candles['minute open'] =  0 S
            
            
            
             i = 555
            
            
            
            candles = df.copy()
            df = candles.copy()
            newCandle = bot.liveBarReceived
            
        def makeMinuteBars( candles , newCandle=None , minCandles=1 ):
            if newCandle:
                candles = candles.append( newCandle,ignore_index=True)
                barsInMin = 12 
                z = barsInMin * minCandles 
                lastBarClose = int(candles.index[-1]//z*z)
                fromLastClose = int(candles.index[-1] - lastBarClose)
                candles.at[len(df)-1,'minute low'] = min( candles[ lastBarClose : lastBarClose + fromLastClose ]['l'])
            else:
                candles['MIN'] = candles['t'].str[8:-2]
                candles['minute low'] = 0
                candles = candles.drop([0,1,2,3,4,5,6])         
                candles.index = np.arange( 0,len(df) )  
                for i in range(0,candles.index[-1],12):
                    for ii in range(0,12):
                        if i!=i+ii:
                            candles.at[i+ii,'minute low']  = min( candles[i:i+ii]['l'] )
                            candles.at[i+ii,'minute high'] = max( candles[i:i+ii]['h] )
                            candles.at[i+ii,'minute open'] = candles.at[i+1,'o']   
                            candles.at[i+ii,'minute close'] = candles.at[ii,'c']                        
                        else: 
                            candles.at[i,'minute low'] = candles.at[i,'l']
                
                
                
                
                
                
                
                
                
                
                
                
                
                minStart = (df.index[-1]//12)*12
                df = df.append( bot.liveBarReceived,ignore_index=True )
                df.index[-1]['c']
                
            
                
                
                
                
                
                
                
                df['MIN'] = df['t'].str[8:-2]    
                df = df.drop([0,1,2,3,4,5,6])         
                df.index = np.arange( 1,len(df)+1 )  
                #df['minute low'] = 0
                for i in range(0,df.index[-1]):
                    print(i)
                    lowestLow = 0 
                    highestHigh = 0
                        
            
            
            
            start = ((df.index[i]//12)*12)
            end = start+11
            if start<0 or end<12:
                lowestLow = min( df[0:12]['l'] )
            else:
                lowestLow = min( df[start:end]['l'] )
            df.at[i+2,'minute low'] = float(lowestLow)
            
            
            
            
            
            
                
                
                
            lowestLow = min( df[0:12]['l'] )
            df.at[i,'minute low'] = float(lowestLow)
            
            
      i = 147      
            
            i = 0
            
            
            df.index[0]
            
            df.index[-1]

            
          

i = 149




        length = df.index[-1]//12






                          # +":" + df['t'].str[10:-2] 
        s = [0,12]
        for i in range(1, len(bars)):
            if df.at[i,'MIN'] > df.at[i-1,'MIN']:
                s[0],s[1] = s[0]+12,s[1]+12
            df.at[i,'min LOW'] = min( df.iloc[s[0]:s[1]]['l'])
    else: 
        
    
    
    
    i = 1
    
    
    m = 12
    for i in range(1,len(df)):  
        if int(df.at[i,'MIN']) > int(df.at[i-1,'MIN']):
            m = m + 12   
        else:
            try:
                ll = min( df.iloc[i+1:m]['l'] )
                df.at[i,'minLow'] = ll
            except Exception as e:
                print(e)

        
        
a = 0         
for i in range(len(bars)):
    if int(df.at[i,'MIN']) > int(df.at[i-1,'MIN']):
        a = a + 12
    Lows = [] 
    for b in range(12):
        Lows = Lows.append( df.at[i:i+b,'l'])
        
        
        
        
        
        
        i = 4
        
        ii = 22
        if miin > df.iloc[i-1,'MIN']:
            twelves = twelves + 12
    
    
    zz= 22
    
    
    
    
    for i in range(len(bars)):
        
    
    
    
    
    m = 0 
    while m < df.shape[0]:
        for i in range( len(df) ):
            if df.iloc[i,'MIN'] > df.iloc[i,'MIN']:
                m = m + 12
                Lows = []
            else:
                for five in range(12):
                    Lows.append( df.iloc[m+five,'l'] ) 
                    df.iloc[i,'LOW'] = min( Lows )
                    
                    
                df.iloc[i,'L'] =   min(df.iloc[m+1,'l'],min(df.iloc[m+1,'l']
                                                            min(df.iloc[m+1,'l']
                                                                min(df.iloc[m+1,'l']
                                                                    min(df.iloc[m+1,'l']
                                                                        min(df.iloc[m+1,'l']
                                                                            min(df.iloc[m+1,'l']
                                                                                min(df.iloc[m+1,'l']
                                                                                    min(df.iloc[m+1,'l']
                                                                                        min(df.iloc[m+1,'l']
                                                                                            min(df.iloc[m+1,'l']
                                                                                                min(df.iloc[m+1,'l']
                
                
                
            df.iloc[i,'L'] =   min(df.iloc[m,'l']  
            if df.iloc[i,'MIN'] > if df.iloc[i,'MIN']
    
    
    
    
    
    df = fiveSecondBars.copy()
    df = bars.copy()
    for i in range(len(df)):
        df.iat[3,'minute'] = df.at[3,'t'][8:-4]
    return df 
    
    
    df['New_Sample'] = df.Sample.str[:1]
    df['minute'] = df['t'].str[8:10] +":" + df['t'].str[10:-2]
    df['minLow'] = df['low']
    
    
 
make1MinuteBars( bars )   
 
    
 
    
    for i in range(len(df)):
        df[]
        bars.shape[0]
    


bars.mean()



'''
enter when... 

    FIVE MIN...
    
    1. derivative of macd difference >= -0.00001 from one bar ago
        [ finding accumulation period in overextended sell-off ]
    
    
    2. ROC derivative > 0 from one bar ago 
        [ clarifying trend is coming out of compression period ]
    
        ONE MIN...
        
        3. derivative of ROC from start of 5min
                bar is positive [example, after 5 10:05-10:10 looking for
                         increasing ROC in 10:11,12,13,14,15]
            [ clarifying smaller time interval is pushing out of 
              accumulation period, pushing up ]
        
        4. DI+ > DI- for one bar or about to cross as measured by 
                slope of linReg of DI+ and DI-
                
                linear regression of DI- from one bar ago < 0
                linear regression of DI+ from one bar ago > 0 
                = DI+[linReg] - DI-[linReg] > 0
            
            [ positive trend is beginning to control direction
              or at least taking control ]
                
        5. adx > 15
            [ trend has integrity ]
        
        6. derivative of macd difference >= -0.00001 from one bar ago
            [ finding accumulation period in overextended sell-off ]
            
            enter at...
            1. limit on close of last bar 
'''
    
    

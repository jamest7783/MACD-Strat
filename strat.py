# -*- coding: utf-8 -*-
"""
trading bot 2

Created on Wed Jun  8 14:46:35 2022
@author: jewittj
"""

from ibapi.wrapper   import EWrapper
from ibapi.client    import EClient 
from ibapi.contract  import Contract 
from ibapi.order     import Order 
from matplotlib      import pyplot as pyl
from talib           import MACD,EMA,ATR,ADX,ROC,LINEARREG,PLUS_DI,MINUS_DI
import pandas            as pd 
import numpy             as np
import threading         as thr
import time              as ti
import datetime          as dt
import warnings          as wrn
import matplotlib.pyplot as pypl
import warnings          as w
w.simplefilter( action='ignore',category=FutureWarning )


# =============================================================================

    # STREAM CLASS 

class stream( EWrapper,EClient ):
    def __init__( self ):
        EClient.__init__( self,self ) 
        self.histOHLCVs  = {} 
        self.newOHLCV    = []
        self.newOHLCVs   = pd.DataFrame( columns=['time','open','high','low','close','volume'] )
        self.positions   = pd.DataFrame( columns=['Account','Symbol','SecType','Currency','Position','Avg cost'])
        self.pNl         = pd.DataFrame( columns=['ReqId','DailyPnL','UnrealizedPnL','RealizedPnL'])
        self.order_df = pd.DataFrame(columns=['PermId', 'ClientId', 'OrderId',
                                              'Account', 'Symbol', 'SecType',
                                              'Exchange', 'Action', 'OrderType',
                                              'TotalQty', 'CashQty', 'LmtPrice',
                                              'AuxPrice', 'Status'])
    def historicalData( self,reqId,cndl ):
        if reqId not in self.histOHLCVs:  
            print( "Retrieved historical data for request",reqId )
            self.histOHLCVs[reqId] = [{ "time"   :cndl.date[-8:].replace(':',''),
                                        "open"   :cndl.open,
                                        "high"   :cndl.high,
                                        "low"    :cndl.low, 
                                        "close"  :cndl.close,
                                        "volume" :cndl.volume }]
        else: self.histOHLCVs[reqId].append({ "time"   :cndl.date[-8:].replace(':',''),
                                              "open"   :cndl.open,
                                              "high"   :cndl.high,
                                              "low"    :cndl.low,
                                              "close"  :cndl.close,
                                              "volume" :cndl.volume })
    def realtimeBar( self,reqId,time,open_,high,low,close,volume,wap,count ):
        super().realtimeBar( reqId,time,open_,high,low,close,volume,wap,count )
        self.newOHLCV = [{ "time":dt.datetime.fromtimestamp(time).strftime('%H%M%S'),
                          "open":open_,"high":high,"low":low,"close":close,"volume":volume }]  
        self.newOHLCVs = self.newOHLCVs.append( self.newOHLCV )
        logTime = self.newOHLCVs.iloc[-1]["time"][:2]+":"+self.newOHLCVs.iloc[-1]["time"][2:4]+":"+self.newOHLCVs.iloc[-1]["time"][4:6]
        print( logTime,"   ",self.newOHLCVs.iloc[-1]["close"],"     <- fresh candle" ) 
    def nextValidId( self,orderId ):
        super().nextValidId( orderId )
        self.nextValidOrderId = orderId
        
    def position( self,account,contract,position,avgCost ):
        super().position( account,contract,position,avgCost )
        dictionary = {  "Account:":account,"Symbol:":contract.symbol, 
                         "SecType":contract.secType,"Currency":contract.currency,
                         "Position":position,"Avg cost":avgCost } 
        self.positions = self.positions.append( dictionary,ignore_index=True )
        
    def positionEnd( self ):
        super().positionEnd() 
        print("PositionEnd")
        
    def pnl( self,reqId,dailyPnL,unrealizedPnL,realizedPnL ):
        super().pnl( reqId,dailyPnL,unrealizedPnL,realizedPnL )
        dictionary = { "ReqId":reqId,"DailyPnL":dailyPnL,"UnrealizedPnL":unrealizedPnL,"RealizedPnL":realizedPnL }
        self.pNl = self.pNl.append( dictionary,ignore_index=True )
    def openOrder(self, orderId, contract, order, orderState):
        
        super().openOrder(orderId, contract, order, orderState)
        dictionary = {"PermId":order.permId, "ClientId": order.clientId, "OrderId": orderId, 
                      "Account": order.account, "Symbol": contract.symbol, "SecType": contract.secType,
                      "Exchange": contract.exchange, "Action": order.action, "OrderType": order.orderType,
                      "TotalQty": order.totalQuantity, "CashQty": order.cashQty, 
                      "LmtPrice": order.lmtPrice, "AuxPrice": order.auxPrice, "Status": orderState.status}
        self.order_df = self.order_df.append(dictionary, ignore_index=True)
 
    
# =============================================================================

    # UTILITIES

def connect():
    stream.run() 
def liveStream( contract ):
    stream.reqRealTimeBars(   reqId=10,       contract=contract, 
                              barSize=5,      whatToShow="TRADES",
                              useRTH=0,       realTimeBarsOptions="" )
def getHistory( req_num,contract,duration,candle_size ):
    stream.reqHistoricalData( reqId=req_num,   contract=contract, 
                              endDateTime='',  durationStr=duration,
                              barSizeSetting=candle_size, 
                              whatToShow='ADJUSTED_LAST',    
                              useRTH=0,         formatDate=1,
                              keepUpToDate=0,   chartOptions=[] )
def defineEquity( ticker,secType="STK",currency="USD",exchange="ISLAND" ):            # make stock object
    contract           = Contract() 
    contract.symbol    = ticker
    contract.secType   = secType
    contract.currency  = currency
    contract.exchange  = exchange
    return contract
def marketOpen():
    Now          = int( dt.datetime.now().strftime("%H%M%S" ))
    marketClose  = 200000
    if Now > marketClose: return False
    else: return True


# =============================================================================

    # STUDIES 

def macd( dataframe ):  
    macd=0
    signal=0
    macd,signal,dataframe['diff']  =MACD(dataframe['close'])  
    return dataframe
def ema( dataframe ):
    dataframe['EMA']  =EMA(dataframe['close'],9)
    return dataframe
def atr( dataframe ):
    dataframe['ATR']  =ATR(dataframe['high'],dataframe['low'],dataframe['close'],14)         
    return dataframe
def adx( dataframe ):
    dataframe['ADX']  =ADX(dataframe['high'],dataframe['low'],dataframe['close'])
    return dataframe
def roc( dataframe ):
    dataframe['ROC']  =ROC(dataframe['close'],9) 
    return dataframe
def diPlus( dataframe ):
    dataframe['DI+']  =PLUS_DI(dataframe['high'],dataframe['low'],dataframe['close']) 
    return dataframe
def diMinus( dataframe ):
    dataframe['DI-']  =MINUS_DI(dataframe['high'],dataframe['low'],dataframe['close']) 
    return dataframe
def derivatives( df ): 
    for i in range(len( df.index )):
        dif    = float(df.at[df.index[i],"diff"])
        dif2   = float(df.at[df.index[i-1],"diff"])
        DER1   = dif-dif2
        time   = df.index[i]          
        time2  = df.index[i-1]
        df.at[df.index[i],"der1"] = DER1
        try:
            DER2 = df.at[time,"der1"]-df.at[time2,"der1"]
            df.at[time,"der2"] = DER2
        except Exception as e: print(e)
    return df 
def parse( interval,studies ):
    for s in range(len( studies )):
        interval = studies[s]( interval ) 
    return interval

# =============================================================================

    # ORDERS 
    
def limitBuy( quantity,price ):
    order               = Order() 
    order.action        = "BUY" 
    order.orderType     = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice      = price
    return order 
def limitSell( quantity,price ):
    order               = Order() 
    order.action        = "SELL"                             
    order.orderType     = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice      = price
    return order

# =============================================================================    

    # ESTABLISH CONNECTION / CREATE INTITIAL DATAFRAMES 

stream = stream()
stream.connect( "127.0.0.1",7497,clientId=1 )                
thread = thr.Thread( target=connect,daemon=True )
thread.start()
 
studies = [ ema,macd,atr,adx,roc,diPlus,diMinus,derivatives ]    
tkr = defineEquity( "AMC" )
 
liveStream( tkr )

getHistory( 12,tkr,"1 D","5 secs" )
getHistory( 1,tkr,"1 D","1 min"   )
getHistory( 5,tkr,"1 D","5 mins"  )

getPNL             = stream.reqPnL( 1,'DU5402333','' )
getCurrentPosition = stream.reqPositions()
getOpenOrders      = stream.reqOpenOrders()

twelfths = parse( pd.DataFrame( stream.histOHLCVs[12] ).set_index( "time" ),studies )
ones     = parse( pd.DataFrame( stream.histOHLCVs[1]  ).set_index( "time" ),studies )
fives    = parse( pd.DataFrame( stream.histOHLCVs[5]  ).set_index( "time" ),studies )  
gap      = True 

capital  = 20000

buyEvents  = [] 
sellEvents = []

currentShares = 0
fullPosition = 20


# =============================================================================

while marketOpen():
    
    # ESTABLISH VARIABLES  
    stream.reqIds(-1)
    #pnlDF         = stream.pNl
    #posPNL        = pnlDF.iloc[-1]["UnrealizedPnL"] 
    #currentShares = round(stream.positions.at[stream.positions.index[-1],"Position"])
    #fullPosition  = round(capital / twelfths.at[twelfths.index[-1],"EMA"])
    
    #if currentShares > 0 : hasPosition = True 
    #else : hasPosition = False
    
    #if currentShares < fullPosition : notFullPosition = True
    #else : notFullPosition = False
    
    # MANAGING & UPDATING CANDLE DATAFRAMES
     
    # DO NOTHING IF DATAFRAME CURRENT 
    freshCndls = parse( stream.newOHLCVs.set_index("time"),studies )
    if int(freshCndls.index[-1]) == int(twelfths.index[-1]): pass 
    else:
        # APPEND FRESH CANDLES TO TWELFTHS DATAFRAME [ CLOSING GAP ]
        if int(freshCndls.index[-1])-int(twelfths.index[-1]) > 5 and gap:
            for index,row in freshCndls.iterrows():
                if int(index) > int(twelfths.index[-1]):
                    twelfths = twelfths.append( freshCndls.loc[index] )
                print( twelfths.index[-1]," <-- new twelfth for closing hist/live gap" )
            twelfths = parse( twelfths,studies )
            print( "             ^-- put studies on after closing gap\n")
            gap = False
            # ti.sleep(1)   
     
        # APPEND FRESH CANDLES TO TWELFTHS DATAFRAME [ INCOMING BARS STACKED ON HISTORICAL BARS ]
        elif int(freshCndls.index[-1]) > int(twelfths.index[-1]):                                   
            twelfths = twelfths.append( freshCndls.iloc[-1] )
            twelfths = parse( twelfths,studies )
            print( twelfths.index[-1],"                 ^ stacked fresh twelfth")
                
            # MAKE NEW ONE MIN BAR FOR ONES DATAFRAME WHEN 1MIN WORTH OF 5SEC BARS 
            if twelfths.index[-1][-2:] == "55" and twelfths.index[-12][-2:] == "00" and twelfths.index[-12] not in ones.index:
                freshOne = pd.DataFrame([{ "time"   : twelfths.index[-12],
                                           "open"   : twelfths.iloc[-12]["open"],
                                           "high"   : max( twelfths.iloc[-12:-1]["high"] ),
                                           "low"    : min( twelfths.iloc[-12:-1]["low"]  ),
                                           "close"  : twelfths.iloc[-1]["close"],
                                           "volume" : sum( twelfths.iloc[-12:-1]["volume"] )}]).set_index("time") 
                ones = ones.append( freshOne )
                ones = parse( ones,studies )
                print( ones.index[-1],"<-- stacked fresh one on ones",ones.iloc[-1] )
    
                # MAKE NEW FIVE MIN BAR FOR FIVES DATAFRAME WHEN 5MIN WORTH OF 5SEC BARS
                if ((twelfths.index[-60][-3:] == "000" and twelfths.index[-1][-3:] == "455") or (twelfths.index[-60][-3:] == "500" and twelfths.index[-1][-3:] == "955")) and twelfths.index[-60] not in fives.index:
                      freshFive = pd.DataFrame([{ "time"   : twelfths.index[-60],
                                                  "open"   : twelfths.iloc[-60]["open"],
                                                  "high"   : max( twelfths.iloc[-60:-1]["high"] ),
                                                  "low"    : min( twelfths.iloc[-60:-1]["low"]  ),
                                                  "close"  : twelfths.iloc[-1]["close"],
                                                  "volume" : sum( twelfths.iloc[-60:-1]["volume"] )}]).set_index("time") 
                      fives = fives.append( freshFive )
                      fives = parse( fives,studies )
                      print( "\t",fives.index[-1],"<-- stacked fresh five on fives",fives.iloc[-1])
                  
                    
# =============================================================================  

    # TRADE LOGIC                       
    #     5 MIN
    #         1. last bar macd difference under 0
    #         2. minimum of macd difference second derivative 
    #     1 MIN
    #         3. last bar macd difference under 0
    #         4. minimum of macd difference second derivative 
    #         5. minimum of rate of change (smoothed?) second derivative
    #     5 SEC
    #         6. rate of change less than 0 
    #     BUY EVENT
    #         buy at close of last bar +/- ATR percentage 
            
    
    
    
            # CANCEL ALL OLD ORDERS 
            
            if(       fives.at[fives.index[-1],"diff"]<0 and 
                      fives.at[fives.index[-1],"der2"]>0 and 
                      fives.at[fives.index[-2],"der2"]<0 and  
                    ones.at[ones.index[-1],"diff"]<0.01 and
                        ones.at[ones.index[-1],"der2"]>0 and 
                        ones.at[ones.index[-2],"der2"]<0 and
                         ones.at[ones.index[-1],"ROC"]<0 and 
                 twelfths.at[twelfths.index[-1],"ROC"]<0 ): #and notFullPosition ):  
            
                    # REQUEST NEW ORDER ID
                    stream.reqIds(-1)
        
                    # CREATE & PLACE NEW BUY ORDER
                    numOrder  = stream.nextValidOrderId
                    numShares = fullPosition - currentShares
                    buyPrice  = round( twelfths.at[twelfths.index[-1],"EMA"] - twelfths.at[twelfths.index[-1],"ATR"]/2,2 )
                    # ti.sleep(1)
                    buyOrder  = stream.placeOrder( numOrder,tkr,limitBuy(numShares,buyPrice ))
                    buyEvents.append( twelfths.index[-1] )
                    print( "** Buy Event" )
            else : print( "NOT buy event" )
                    
            if( fives.at[fives.index[-1],"diff"]>0 and 
                fives.at[fives.index[-1],"der2"]<0 and 
                fives.at[fives.index[-2],"der2"]>0 ): 
                
                    # REQUEST NEW ORDER ID 
                    stream.reqIds(-1)
 
                    # CREATE & PLACE NEW BUY ORDER
                    numOrder  = stream.nextValidOrderId
                    sellPrice = round( twelfths.at[twelfths.index[-1],"EMA"] )
                    # ti.sleep(1)
                    sellOrder = stream.placeOrder( numOrder,tkr,limitSell(currentShares,sellPrice ))
                    sellEvents.append( twelfths.index[-1] )
                    print( "** Sell Event \n\n" )
            else : print( "NOT sell event","\n\n" )
                
                
# =============================================================================  



#and notFullPosition ):  
  # and hasPosition ):



















                 
                
# =============================================================================
#         
# =============================================================================
    
        
     
    
    
        
         
                      
                      entryPrice = round(fives.at[fives.index[-1],"EMA"],2)+0.05
                      numShrs    = 20 
                      
                      stream.reqIds(-1)
                      ordrNum   = stream.nextValidOrderId
                      buyOrder  = stream.placeOrder( ordrNum,tkr,limitBuy(numShrs,entryPrice ))
                      ti.sleep(1)
                      
                      stream.reqIds(-1)
                      ti.sleep(1)
                      ordrNum   = stream.nextValidOrderId
                      sellOrder = stream.placeOrder( ordrNum,tkr,limitSell(numShrs,entryPrice+0.03 ))
                  
                  
        for i in range(len(f)):
            for a in range(len(o)):
                if int(o[i])-int(f[i])<=400 and int(o[i])-int(f[i])>0:     
                    print(f[i]," --> ",o[i])
        
        
         
         
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    

        
    f = []     
    for i in range(len(fives)):
        if fives.at[fives.index[i],"diff"]<0:
            if fives.at[fives.index[i],"der2"]>0 and fives.at[fives.index[i-1],"der2"]<0: 
                f.append(fives.index[i])
                print(fives.index[i])
            
    o = []        
    for a in range(len(ones)):
        if ones.at[ones.index[a],"diff"]<0.001: 
            if ones.at[ones.index[a],"der2"]>0 and ones.at[ones.index[a-1],"der2"]<0: 
                if ones.at[ones.index[a],"ROC"]<0:
                    o.append(ones.index[a])
                    print(ones.index[a])
    
    t = [] 
    for b in range(len(twelfths)):
        if twelfths.at[twelfths.index[b],"ROC"]<0:
            t.append(twelfths.index[b])
            print(twelfths.index[b])
        
         
               
            
            
            print(fives.at[fives.index[i1], "diff"])
            print(fives.at[fives.index[i+1], "diff"])
            
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # 5MIN
    fiveDiffUnderZero     = -1
    fiveDiffScndInfl      = -1 #second derivative
    
    # 1MIN
    oneDiffUnderZero      = -1
    oneDiffInfl           = -1 #first derivative 
    oneROCUnderZero       = -1
    
    # 5SEC
    twelfthROCUnderZero   = -1
    
    if fives.at[fives.index[-1],"diff"]<0:                                                                     fiveDiffUnderZero = 1       
    if fives.at[fives.index[-1],"der2"]>0 and fives.at[fives.index[-2],"der2"]<0:                                   fiveDiffInfl = 1
    
    if ones.at[ones.index[-1],"diff"]<0.001:                                                                 oneDiffUnderZeroish = 1
    if ones.at[ones.index[-1],"der2"]>0 and ones.at[ones.index[-2],"der2"]<0:                                        oneDiffInfl = 1
    if ones.at[ones.index[-1],"ROC"]<0 or ones.at[ones.index[-2],"ROC"]<0 or ones.at[ones.index[-3],"ROC"]<0:    oneROCUnderZero = 1
    
    if twelfths.at[twelfths.index[-1],"ROC"]<0:                                                              twelfthROCUnderZero = 1
    if twelfths.at[twelfths.index[-1],"ROC der"]>0:                                                               twelfthROCInfl = 1
    
    buyEvent = fiveDiffUnderZero+fiveDiffInfl+oneDiffUnderZero+oneDiffInfl+oneROCUnderZero+twelfthROCUnderZero
    if buyEvent == 6:
        buyEvent=True
                      
                 

                 
            
                
              
                ROC()
               
                
              for i in range(len(fives)):
                  if fives.at[fives.index[i],"diff"]<0:
                      if fives.at[fives.index[i],"der2"]>0 and fives.at[fives.index[i-1],"der2"]<0:
                        print(fives.index[i])
                        print(fives.at[fives.index[i],"der2"])
                        print(fives.at[fives.index[i-1],"der2"],"\n\n")
                        
                        for a in range(len(ones)): 
                            if ones.at[ones.index[a],"diff"]<0.001: 
                                if ones.at[ones.index[a],"der2"]>0 and ones.at[ones.index[a-1],"der2"]<0:      
                                    print(ones.index[a])
                  
                
              
                
              
                
              
                
              
                
              
                
              
                # ONLY IF NEWE FIVE EXAMINE TRADE LOGIC 
                  if( fives.at[fives.index[-1],"diff"]<0 and fives.at[fives.index[-1],"der2"]>0 and fives.at[fives.index[-2],"der2"]<0 and
                      ones.at[ones.index[-1],"diff"]<0   and ones.at[ones.index[-1],"der2"]>0   and ones.at[ones.index[-1],"der2"]<0 ):
                      
                      
                      
                      
                      if fives.at[fives.index[-1],"diff"]<0:
                          
                      if fives.at[fives.index[-1],""]
                      
                      
                      
                      
                      
                      
                      
                      
                      entryPrice = round(fives.at[fives.index[-1],"EMA"],2)+0.05
                      numShrs    = 20 
                      
                      stream.reqIds(-1)
                      ordrNum   = stream.nextValidOrderId
                      buyOrder  = stream.placeOrder( ordrNum,tkr,limitBuy(numShrs,entryPrice ))
                      ti.sleep(1)
                      
                      stream.reqIds(-1)
                      ti.sleep(1)
                      ordrNum   = stream.nextValidOrderId
                      sellOrder = stream.placeOrder( ordrNum,tkr,limitSell(numShrs,entryPrice+0.03 ))
                  
                  
                  
             
                  fives
                  1. macd difference below 0 and                                if fives.at[fives.index[-1],"diff"]<0:                                                                   fiveDiffUnderZero   
                  2. last second derivative of diiference positive and          if fives.at[fives.index[-1],"der2"]>0 and fives.at[fives.index[-2],"der2"]<0:                            fiveDiffInfl     
                  3. lastx2 second derivative negative 
                  
                  ones
                  4. last ones macd difference under zero and                   if ones.at[ones.index[-1],"diff"]<0:                                                                      oneDiffUnderZero                                                                                                                                                       
                  4. last second derivative of diiference positive and          if ones.at[ones.index[-1],"der2"]>0 and ones.at[ones.index[-2],"der2"]<0:                                 oneDiffInfl    
                  5. lastx2 second derivative negative                          
                  6. last ROC first derivative positive and                     if ones.at[ones.index[-1],"der2"]>0 and ones.at[ones.index[-2],"der2"]<0:                                 oneROCInfl          <-- this may be too difficult 
                  7. lastx2 ROC first derivative negative   
                  8. ROC has been below zero in the last three candles          if ones.at[ones.index[-1],"ROC"]<0 or ones.at[ones.index[-2],"ROC"]<0 or ones.at[ones.index[-3],"ROC"]<0  oneROCUnderZero     <-- just this would allow more time 
                  
                  twelfths 
                  9. ROC below zero and                                         if twelfths.at[twelfths.index[-1]"ROC"]<0:                                                                twelfthROCUnderZero
                  10. buy at ask +0.01                                          [alternative: buy at ema,ema+0.01,ema-0.01]
                  
                  
                  
                  
              
                  
                  
                  
# =============================================================================
# 
#     will work a lot better with etf's (smoother)
#
#     if rate of change is also increasing 
#     if macd diff is below zero 
#
#     if macd diff has a negative linear slope linear regression line longer than 3 candles 
#     if 
#
#
#
#
# =============================================================================
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
              
               
              
              lastder2 = fives.at[fives.index[-2],"der2"]
              crntder2 = fives.at[fives.index[-1],"der2"] 
            
              if lastder2<0 and crntder2>0: 
                ema = round(twelfths.at[twelfths.index[-1],"EMA"],2)
                lastClose = twelfths.at[twelfths.index[-1],"close"]
                if lastClose<ema:
                    atrFrom  = round(twelfths.at[twelfths.index[-1],"EMA"]+twelfths.at[twelfths.index[-1],"ATR"]/2,2)
                elif lastClose>ema:
                    atrFrom = round(twelfths.at[twelfths.index[-1],"EMA"]-twelfths.at[twelfths.index[-1],"ATR"]/2,2)
                
                shares = 20
                
                stream.reqIds(-1)
                oid = stream.nextValidOrderId
                stream.placeOrder( oid,tkr,limitBuy(shares,ema) )
                ti.sleep(1)
                 
                
                stream.reqIds(-1)
                ti.sleep(1)
                oid = stream.nextValidOrderId
                stream.placeOrder( oid,tkr,limitSell(shares,ema+0.1) )

        

# =============================================================================   
        





stream.reqIds(-1)
orderId = stream.nextValidOrderId

buyOrder = stream.placeOrder( orderId,tkr,lb )



stream.reqPnL( 1,'DU5402333','' )
pnlDF = stream.pNl
pnl = pnlDF.iloc[-1]["UnrealizedPnL"]/20

stream.reqPositions()
pos = stream.positions




stream.reqAccountSummary(1, "All", "$LEDGER:ALL")


stream.reqOpenOrders()
stream.positions


 

check pnl 







newBuyOrder = stream.placeOrder( oid,tkr,limitBuy(1,price+.1) )
newSellOrder = stream.placeOrder( oid,tkr,limitSell(10,price+.1) )

stream.reqAccountSummary(1, "All", "$LEDGER:ALL")
stream.reqPnL( 8,'DU5402333','' )

orderDF = stream.order_df
pos = stream.positions 
pnl = stream.pNl

stream.reqOpenOrders()

 
eP = round(twelfths.iloc[-1]["EMA"],2)


lb = limitBuy( 20,eP )

price = round(twelfths.at[twelfths.index[-1],"EMA"]+0.10,2)

def limitBuy( quantity,price ):
    order               = Order() 
    order.action        = "BUY" 
    order.orderType     = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice      = price
    return order 
def limitSell( quantity,price ):
    order               = Order() 
    order.action        = "SELL"                                # orders
    order.orderType     = "LMT"
    order.totalQuantity = quantity
    order.lmtPrice      = price
    return order









        fives.at[time,"der1"]
    
    
    liveCndls = stream.newOHLCVs.set_index("time")
    if int(liveCndls.index[-1]) > int(twelfths.index[-1]):
        twelfths = twelfths.append( liveCndls.iloc[-1] )
        
        
        
        
        
        
        pd.DataFrame( [stream.newOHLCVs[-1]] ) 
        
        twelfths = twelfths.append( stream.newOHLCVs[-1] )
        
    twelfths = twelfths.set_index("time")
    
    
    
    if((stream.newOHLCVs[-60]["time"][-3:] == "000" and stream.newOHLCVs[-1]["time"][-3:] == "455" or
        stream.newOHLCVs[-60]["time"][-3:] == "500" and stream.newOHLCVs[-1]["time"][-3:] == "955" )):
        
        freshFive = { "time"  : stream.newOHLCVs[-60]["time"],
                      "open"  : stream.newOHLCVs[-60]["open"],
                      "high"  : max( stream.newOHLCVs["high"][-60:-1] ),
                      "low"   : min( stream.newOHLCVs[-60:-1]["low"]  ),
                      "close" : stream.newOHLCVs[-1]["close"] }
            
            
            
            }
        
        







x = stream.pNl
x = stream.positions













for index,row in intervals[0].iterrows():
    #print(index,intervals[0].at[index,"close"])
    if str(index)[-3:] == "000" or str(index)[-3:] == "500": 
        print(index,intervals[0].at[index,"close"])
        print("start of five^^\n")
    if str(index)[-3:] == "955" or str(index)[-3:] == "455": 
        print(index,intervals[0].at[index,"close"])
        print("end of five^^\n")

    
    if intervals[0].iloc[-1]
          i = 67
intervals = applyStudies( [twelfths,ones,fives],studies )

for i in range(len(stream.newOHLCVs)):
    if( stream.newOHLCVs[i-59]["time"][-3:] == "000" and stream.newOHLCVs[i]["time"][-3:] == "455" or
       stream.newOHLCVs[i-59]["time"][-3:] == "500" and stream.newOHLCVs[i]["time"][-3:] == "955"):
       print(stream.newOHLCVs[i-59]["time"], ">>", stream.newOHLCVs[i]["time"])
       
n=1
while n!=3 :
    if( stream.newOHLCVs[-60]["time"][-3:] == "000" and stream.newOHLCVs[-1]["time"][-3:] == "455" or
        stream.newOHLCVs[-60]["time"][-3:] == "500" and stream.newOHLCVs[-1]["time"][-3:] == "955"):

       print("begin:", stream.newOHLCVs[-60]["time"]," open: ",stream.newOHLCVs[-60]["open"], ">> end:", stream.newOHLCVs[-1]["time"], "close: ", stream.newOHLCVs[-1]["close"])
       

 

x = stream.newOHLCVs



        
        type(stream.newOHLCVs)
        
        stream.newOHLCVs[1]
        
        
if str(index)[-3:] == "000" or str(index)[-3:] == "500": 

x = print(stream.newOHLCVs[-60]["time"],stream.newOHLCVs[-1]["time"])



# testing to generate buy signal (t/f)
for df in intervals:
    lastScndDer = 0
    for index,rows in df.iterrows():
        if df.at[index,'second derivative']>0 and lastScndDer<0:
            df.at[index,"BUY"] = True
        else: df.at[index,"BUY"] = False
        lastScndDer = df.at[index,'second derivative']
        
        
        
        
        
        
        
     fives = intervals[2]   
     twelfths = intervals[0] 

if fives.iloc[-1]["second derivative"] > 0 and fives.iloc[-2]["second derivative"] < 0:
    
    lastEma             = twelfths.iloc[-1]["EMA"]
    lastEmaPlusHalfATR  = twelfths.iloc[-1]["EMA"] + twelfths.iloc[-1]["ATR"]/2
    lastClose           = twelfths.iloc[-1]["close"]
    
    stream.placeOrder( lastEma            )
    stream.placeOrder( lastEmaPlusHalfATR )
    stream.placeOrder( lastClose          ) 
    
    
    

i                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             

# =============================================================================
# 
# Buy Event 
#     if second derivative of 5 bar's macd diff from two bars ago was 
#       negative and this last one was positive
#     after close of that previous 5 bar, after close of previous 5.15 bar        
#       limit on last 9 ema + 1/2 atr 
#       limt on last 9 ema 
#       limit on close of last bar  
#
# =============================================================================
#
# Sell Event 
#   some at +0.10     
#   some at maximum of rate of change  
#       limit order on last close  
#
# =============================================================================      
#
# Stop Loss Event
#    all or remaining at crossover of DI+ and DI-
#
# =============================================================================         
        
        
       
































for df in intervals:
    downCnt = 0
    upCnt   = 0
    for index,row in df.iterrows():
        if df.at[index,'first derivative']<0:
            downCnt -= 1
            upCnt = 0
        if df.at[index,'first derivative']>0:
            downCnt = 0  
            upCnt += 1
        else: pass 
        df.at[index,"slope+"] = upCnt
        df.at[index,"slope-"] = downCnt
               
       
        
       
        

df = intervals[2]
pypl.plot(df.index,df["slope+"])
pypl.plot(df.index,df["slope-"])
pypl.plot(df.index[60:90],df[60:90]["DIFF"])
pypl.plot(df.index[60:90],df[60:90]["first derivative"])
pypl.plot(df.index[60:90],df[60:90]["second derivative"])
pypl.axhline(y=0, color='r', linestyle='-')
pypl.grid()
pypl.plot(0)

while marketOpen(): 
    if timeGap(): closeGap( stream.newOHLCVs,intervals )
    else: 
        intervals = stackCndls( stream.newOHLCVs,intervals )
    
        if noPosition():
            
    
            
            
      
               fives.at[len(fives)-1,"second derivative"]<0 and 
               fives.at[len(fives)-2,"second derivative"]>0 and 
        
        
        



            if fives.at[len(fives)-1,"d"] > some negative number and:
               fives.at[len(fives)-1,"d"]



pypl.plot(fives[70:95]["first derivative"])
pypl.plot(fives[70:95]["second derivative"])
pypl.plot(fives[70:95]["DIFF"])
pypl.axhline(y=0, color='r', linestyle='-')
pypl.grid()
#inflection points check minimum at 70


fives = fives.set_index("time")

 




















# orders 
# position information
 
stream.reqPositions()
posdf = stream.positions

stream.reqPnL( 1,"DU5402333","" )
pnldf  = stream.pNl

posdf.iloc[-1]["Avg cost"]
pnldf.iloc[-1]["UnrealizedPnL"]/posdf.iloc[-1]["Position"]

stream.reqOpenOrders()
order_df = stream.order_df

stream.reqIds(-1)

oId = stream.nextValidOrderId


order = Order()
order.action = "BUY"
order.orderType = "MKT"
order.totalQuantity = 10

ticker = "F"
ticker = defineEquity( ticker )
stream.placeOrder( oId,ticker,order )






    
# going to need to fix ( use tickData instead? )>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# =============================================================================
# def closeGap( newCndls,intervals ):
#     for i in range(len( newCndls )):
#         if int( newCndls[i]["time"]) > int(intervals[0].iloc[-1]["time"]):
#             intervals[0] = intervals[0].append( newCndls[i],ignore_index=True )
#             if intervals[0].iloc[-1]['time'][4:]=="55" and intervals[0].iloc[-12]['time'][4:]=="00":
#                 intervals[1] = intervals[1].append([{ "time"  : intervals[0].iloc[-12]['time'],
#                                                       "open"  : intervals[0].iloc[-12]["open"],
#                                                       "high"  : max( intervals[0][-12:-1]["high"]), 
#                                                       "low"   : min( intervals[0][-12:-1]["low"]),
#                                                       "close" : intervals[0].iloc[-1]['close'],
#                                                       "volume": sum( intervals[0][-12:-1]["volume"]) }])
#             if( int(intervals[0].iloc[-1]['time']) - int(intervals[0].iloc[-60]['time']) == 455 and 
#                (intervals[0].iloc[-60]['time'][3:]=="500" or intervals[0].iloc[-60]['time'][3:]=="000" )):                
#                 intervals[2] = intervals[2].append([{ "time"  : intervals[2].iloc[-60]['time'],
#                                                       "open"  : intervals[2].iloc[-60]["open"],
#                                                       "high"  : max( intervals[2].iloc[-60:-1]["high"]), 
#                                                       "low"   : min( intervals[2].iloc[-60:-1]["low"]),
#                                                       "close" : intervals[2].iloc[-1]['close'],
#                                                       "volume": sum( intervals[2][-60:-1]["volume"]) }])
#     applyStudies( intervals,studies )
#     return intervals
# =============================================================================
# =============================================================================
# 
# def stackCndls( newCndls,intervals ):
#     if int( newCndls[-1]["time"]) > int(intervals[0].iloc[-1]["time"]):
#             intervals[0] = intervals[0].append( newCndls[-1],ignore_index=True )
#             if intervals[0].iloc[-1]['time'][4:]=="55" and intervals[0].iloc[-12]['time'][4:]=="00":
#                 intervals[1] = intervals[1].append([{ "time"  : intervals[0].iloc[-12]['time'],
#                                                       "open"  : intervals[0].iloc[-12]["open"],
#                                                       "high"  : max( intervals[0][-12:-1]["high"]), 
#                                                       "low"   : min( intervals[0][-12:-1]["low"]),
#                                                       "close" : intervals[0].iloc[-1]['close'],
#                                                       "volume": sum( intervals[0][-12:-1]["volume"]) }])
#                 if( int(intervals[0].iloc[-1]['time']) - int(intervals[0].iloc[-60]['time']) == 455 and 
#                    (intervals[0].iloc[-60]['time'][3:]=="500" or intervals[0].iloc[-60]['time'][3:]=="000" )):                
#                     intervals[2] = intervals[2].append([{ "time"  : intervals[2].iloc[-60]['time'],
#                                                           "open"  : intervals[2].iloc[-60]["open"],
#                                                           "high"  : max( intervals[2].iloc[-60:-1]["high"]), 
#                                                           "low"   : min( intervals[2].iloc[-60:-1]["low"]),
#                                                           "close" : intervals[2].iloc[-1]['close'],
#                                                           "volume": sum( intervals[2][-60:-1]["volume"]) }])
#     applyStudies( intervals,studies )
#     return intervals
# =============================================================================



# Version 1.3
import pandas as pd
import numpy as np

from Calculate_indicators import Calculate_indicators

class Trade_logic(): #Repository of diffrent trading strategies WARNING!!! None of them work!!! Use only as examples.
    
    def __init__(self, dataframe):
        """
        dataframe: Pandas dataframe, result from calling Harvest_data.get_data()
        """
        self.data = dataframe
        
    def buy_and_hodl(self):
        """
        For strategy comparison. Used by Analyze_backtest to caluculate account value by only buying and holding.
        """
        hodl = []
        for i in list(self.data['Close']):
            hodl.append('SELL')
        hodl[0] = 'BUY'
        self.data['Trades-BnH'] = pd.DataFrame(hodl)
    
    def simple_mean_reversion(self, n = 20, price='Close', mean='SMA', buy_limit='Sigma1_low'):
        """
        Mean reversion strategy, buys when price crosses buy_limit value, sells when price returns to the mean.
        ### WARNING - No stoploss, buy triggers on UPWARDS cross of buy limit ###
        
        n: Number of datapoints included (last n datapoints). Integer. Tipicaly 20, SMA20
        price: Column name with current price. String. Typicaly 'Close'.
        mean: Column name with current mean price. String. Typicaly 'SMA' - simple moving average
        buy_limit: Column name which triggers buy signal, when price crosses back to mean it triggers sell. String.
        """
        #Indicator preparation 
        indicators = Calculate_indicators(self.data)
        indicators.bollinger_bands(n=n, sigma1=True, sigma2=True, sigma3=True)
        buy_limit = list(indicators.data[buy_limit])
        mean = list(indicators.data[mean])
        Close = list(self.data[price])
        
        #Strategy
        trades = []
        state = ''
        for i in range(1, len(buy_limit)):
            if state != 'BUY':
                if Close[i-1] < buy_limit[i-1] and Close[i] >= buy_limit[i]:
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if Close[i-1] < mean[i-1] and Close[i] >= mean[i]:
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
                              
        self.data['Trades-simple_mean_reversion'] = pd.DataFrame(trades)
        
        return
        
    def ema_crossover(self, long=48, short=12):
        """
        EMA crossover strategy, when EMA_short crosses EMA_long upwards a buy signal is triggered, when crossed down sell.

        long, short: Length of calculation period for each ema (n last values). Integer.
        """
        #Indicator preparation 
        indicators = Calculate_indicators(self.data)
        indicators.EMA(name='EMA_long', days=long)
        indicators.EMA(name='EMA_short', days=short)
        EMA_long = list(indicators.data['EMA_long'])
        EMA_short = list(indicators.data['EMA_short'])
        
        #Strategy
        trades = []
        state = ''
        for i in range(1, len(EMA_short)):
            if state != 'BUY':
                if EMA_short[i-1] < EMA_long[i-1] and EMA_short[i] >= EMA_long[i]:
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if EMA_long[i-1] < EMA_short[i-1] and EMA_long[i] >= EMA_short[i]:
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
                              
        self.data['Trades-ema_crossover'] = pd.DataFrame(trades)
        
        return
    
    def ATR_mean_reversion(self, n=14, k=2): #Zanič ne dela
        """
        Mean reversion with the lower buy level of n * ATR.

        k: coefficient multplying ATR. Integer.
        """
        #Indicator preparation 
        indicators = Calculate_indicators(self.data)
        indicators.ATR(n)
        indicators.EMA(days=n)
        Close = list(self.data['Close'])
        ATR = list(indicators.data['ATR'])
        EMA = list(indicators.data['EMA_long'])
        
        #Strategy
        trades = []
        state = ''
        
        for i in range(1, len(ATR)):
            if state != 'BUY':
                if Close[i-1] < (EMA[i-1] - (k * ATR[i-1])) and Close[i] >= (EMA[i] - (k * ATR[i])):
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if Close[i] >= EMA[i]:
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
        
        self.data['Trades-ATR_mean_reversion'] = pd.DataFrame(trades)
        
        return trades
    
    def MACD_trender(self, long=26, short=12, signal=9):
        """
        MACD crossover trader. When signal line passes above MACD buy, cross down sell.

        long, short, signal: Defines last n datapoints included. Integer. Typicaly 26, 12 and 9.
        """

        #Indicator preparation 
        indicators = Calculate_indicators(self.data)
        indicators.MACD(long, short, signal)
        Close = list(self.data['Close'])
        MACD = list(indicators.data['MACD'])
        Signal = list(indicators.data['Signal'])
        
        #Strategy
        trades = []
        buy_price = Close[0]
        state = ''
        
        for i in range(0, len(Close)):
            if state != 'BUY':
                if MACD[i-1] < Signal[i-1] and MACD[i] >= Signal[i]:
                    buy_price = Close[i]
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if (MACD[i-1] > Signal[i-1] and MACD[i] <= Signal[i] and Close[i] > buy_price):
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
        
        self.data['Trades-MACD_trender'] = pd.DataFrame(trades)
        
        return
    
    def custom_1(self, n=3):
        """
        Testing random ideas.

        """
        Close = list(self.data['Close'])
        Low = list(self.data['Low'])
        
        trades = []
        buy_price = Close[0]
        state = ''
        
        trades.append('None')
        trades.append('None')
        trades.append('None')
        
        for i in range(3, len(Close)):
            if state != 'BUY':
                if (Low[i-3] > Low[i-2] and Low[i-2] > Low[i-1]):
                    buy_price = Close[i]
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if (Close[i-1] > Close[i] and Close[i] > buy_price):
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
        
        self.data['Trades-Custom_1'] = pd.DataFrame(trades)
        
        return

    def custom_2(self, n=30, procent = 0.2):
        """
        Testing random ideas.

        """
        Close = list(self.data['Close'])
        Low = list(self.data['Low'])
        High = list(self.data['High'])

        trades = []
        buy_price = Close[0]
        state = ''
        
        trades = [trades.append('None') for i in range(n)]
       
        for i in range(n, len(Close)):
            if state != 'BUY':
                if (((min(Low[(i-n):(i-1)])) * (1 + procent)) < Close[i]):
                    buy_price = Close[i]
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if (((max(High[(i-n):(i-1)])) * (1 - procent)) > Close[i] and Close[i] > buy_price):
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')

        
        self.data['Trades-Custom_2'] = pd.DataFrame(trades)
        return
       
    def count_peaks(self, n=6, days_long=14, days_short=9): #Zanič ne dela
        """
        Counting peaks strategy.

        n: Number of datapoints included (last n datapoints). Integer.
        days_long, days_short: Number of datapoints included in Volume ema calculation. Integer.
        """

        indicators = Calculate_indicators(self.data)
        indicators.num_peaks(n, price = 'Close')
        indicators.EMA(prices='Volume', name='Vol_long', days=days_long)
        indicators.EMA(prices='Volume', name='Vol_short', days=days_short)
        Close = list(self.data['Close'])
        num_max_values = list(indicators.data['num_max_values'])
        num_min_values = list(indicators.data['num_min_values'])
        Vol_long = list(self.data['Vol_long'])
        Vol_short = list(self.data['Vol_short'])
        
        trades = []
        state = ''
       
        trades.append('None')
    
        for i in range(1, len(Close)):
            if state != 'BUY':
                if  (num_min_values[i-1] > num_max_values[i-1] and num_min_values[i] < num_max_values[i] and Vol_short[i] > Vol_long[i]):
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if (num_min_values[i-1] < num_max_values[i-1] and num_min_values[i] > num_max_values[i]):
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
        
        self.data['Trades-count_peaks'] = pd.DataFrame(trades)
 
        return

    def count_peaks_2(self, peak=5, n = 12, price='Close'):
        """
        Improved count peaks strategy.

        peak: Sell triggers when num_peaks_dif exceeeds peak. Integer.
        n: Number of datapoints included (last n datapoints). Integer.
        price: Column name on which to perform num_peaks_diff. String.
        """
        Close = list(self.data['Close'])
        indicators = Calculate_indicators(self.data)
        indicators.num_peaks_diff(n, price = price)
        num_peaks_diff = list(self.data['num_peaks_diff'])
        
        trades = []
        state = ''
       
        trades.append('None')
    
        for i in range(1, len(Close)):
            if state != 'BUY':
                if  (num_peaks_diff[i-1] <= 0 and num_peaks_diff[i] >= 0):
                    trades.append('BUY')
                    state = 'BUY'
                else:
                    trades.append('None')
            elif state != 'SELL':
                if (num_peaks_diff[i] >= peak):
                    trades.append('SELL')
                    state = 'SELL'
                else:
                    trades.append('None')
        
        self.data['Trades-count_peaks'] = pd.DataFrame(trades)
 
        return

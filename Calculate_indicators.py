# Version 1.3
import pandas as pd
import numpy as np

class Calculate_indicators(): #Repository for functions to calculate indicators
    
    def __init__(self, dataframe):
        """
        dataframe: Pandas dataframe, result from calling Harvest_data.get_data()
        """
        self.data = dataframe
        self.data['Close'] = pd.to_numeric(self.data["Close"], downcast="float")
        self.data['Open'] = pd.to_numeric(self.data["Open"], downcast="float")
        self.data['High'] = pd.to_numeric(self.data["High"], downcast="float")
        self.data['Low'] = pd.to_numeric(self.data["Low"], downcast="float")
        self.data['Volume'] = pd.to_numeric(self.data["Volume"], downcast="float")
        
        
    def bollinger_bands(self, n=20, sigma1=False, sigma2=True, sigma3=False):
        """
        Adds columns for bollinger bands.

        n: Number of datapoints included (last n datapoints). Tipicaly 20, SMA20
        sigma1, sigma2, sigma3: Which band will be added to the dataframe. How many standard deviations +/- from average. Integer. 1x sigma->68,2%, 2x sigma->96%, 3x sigma->99%
        """
        self.data['TP'] = (self.data['Close'] + self.data['Low'] + self.data['High'])/3
        self.data['std'] = self.data['TP'].rolling(n).std(ddof=0)
        self.data['SMA'] = self.data['TP'].rolling(n).mean()
        
        if sigma1 == True:
            self.data['Sigma1_high'] = self.data['SMA'] + 1*self.data['std']
            self.data['Sigma1_low'] = self.data['SMA'] - 1*self.data['std']
        else:
            pass
            
        if sigma2 == True:
            self.data['Sigma2_high'] = self.data['SMA'] + 2*self.data['std']
            self.data['Sigma2_low'] = self.data['SMA'] - 2*self.data['std']
        else:
            pass
            
        if sigma3 == True:
            self.data['Sigma3_high'] = self.data['SMA'] + 3*self.data['std']
            self.data['Sigma3_low'] = self.data['SMA'] - 3*self.data['std']
        
        self.data = self.data.drop(columns=['TP', 'std'])
        return

    def MACD(self, long=26, short=12, signal=9):
        """
        Calculates indicator MACD.

        long, short, signal: Defines last n datapoints included. Integer. Typicaly 26, 12 and 9.
        """
        self.EMA(name='ema_long', days=long) #26-day (long) EMA of Close price
        self.EMA(name='ema_short', days=short) #12-day (short) EMA of Close price cene
        self.data['MACD'] = self.data['ema_short'] - self.data['ema_long'] # MACD = 12-Period EMA − 26-Period EMA
        
        self.EMA(prices='MACD', name='Signal', days=signal) # 9-Day EMA of the MACD for Signal line
        self.data = self.data.drop(columns=['ema_long', 'ema_short'])
        return
        
    def RSI(self, n=14):
        """
        Calculates RSI indicator.

        n: Defines last n datapoints included in calculation. Integer. Typicaly 14
        """
        def rma(x, n, y0):
            a = (n-1) / n
            ak = a**np.arange(len(x)-1, -1, -1)
            return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a**np.arange(1, len(x)+1)]

        self.data['change'] = self.data['Close'].diff()
        self.data['gain'] = self.data['change'].mask(self.data['change'] < 0, 0.0)
        self.data['loss'] = -self.data['change'].mask(self.data['change'] > 0, -0.0)
        self.data['avg_gain'] = rma(self.data.gain[n+1:].to_numpy(), n, np.nansum(self.data.gain.to_numpy()[:n+1])/n)
        self.data['avg_loss'] = rma(self.data.loss[n+1:].to_numpy(), n, np.nansum(self.data.loss.to_numpy()[:n+1])/n)
        self.data['rs'] = self.data.avg_gain / self.data.avg_loss
        self.data['RSI'] = 100 - (100 / (1 + self.data.rs))
        self.data = self.data.drop(columns=['change', 'gain', 'loss', 'avg_gain', 'avg_loss', 'rs'])
        return
    
    
    def EMA(self, prices='Close', name='EMA_long', add_column = True, days=14):
        """
        Calculates indicator EMA (Exponential Moving Average).

        prices: Column name from dataframe on which to perform calculation. String. Typicaly 'Close'.
        add_column: If True it adds column to dataframe. If False the function call returns a list
        name: If add_column = True, name of the new column. String. Example 'EMA_long'.
        days: Defines last n datapoints included in calculation. Integer.
        """
        smoothing = 2 / float(1 + days) #Calculates smoothing factor
        
        def calculate_ema(prices, days, smoothing):
            ema = []
            sma = sum(prices[:days]) / days
            for i in range(days):
                ema.append(sma)
                
            for price in prices[days:]:
                ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
            return ema
        
        ema = calculate_ema(list(self.data[prices].astype('float')), days, smoothing)
        
        if add_column == True:
            self.data[name] = ema
        elif add_column == False:
            return ema
        else:
            raise Exception('add_column must be True or False!!!')
        return
    
    def ATR(self, n=14):
        """
        Calculates indicator ATR (Average True Range).

        n: Defines last n datapoints included in calculation. Integer. Typicaly 14.
        """
        high_low = self.data['High'] - self.data['Low']
        high_Close = np.abs(self.data['High'] - self.data['Close'].shift())
        low_Close = np.abs(self.data['Low'] - self.data['Close'].shift())
        ranges = pd.concat([high_low, high_Close, low_Close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(n).sum()/n
        self.data['ATR'] = atr
        return
    
    def ADX(self, n=14):
        """
         Calculates indicator ADX (Average Directional Indicator). Returns +DMI, -DMI and ADX, + and - tell trend direction, adx tells strength of trend, 0 to 100.

        n: Defines last n datapoints included in calculation. Integer. Typicaly 14.
        """
        plus_dm = self.data['High'].diff()
        minus_dm = self.data['Low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
    
        tr1 = pd.DataFrame(self.data['High'] - self.data['Low'])
        tr2 = pd.DataFrame(abs(self.data['High'] - self.data['Close'].shift(1)))
        tr3 = pd.DataFrame(abs(self.data['Low'] - self.data['Close'].shift(1)))
        frames = [tr1, tr2, tr3]
        tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
        atr = tr.rolling(n).mean()
    
        plus_di = 100 * (plus_dm.ewm(alpha = 1/n).mean() / atr)
        minus_di = abs(100 * (minus_dm.ewm(alpha = 1/n).mean() / atr))
        dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
        adx = ((dx.shift(1) * (n - 1)) + dx) / n
        adx_smooth = adx.ewm(alpha = 1/n).mean()
        self.data['+DMI'] = plus_di
        self.data['-DMI'] = minus_di
        self.data['ADX'] = adx_smooth
        return
        
    def num_peaks(self, n=6, price = 'Close'):
        """
        Custom indicator. It counts a number of highest highs and lowest lows achieved in a series of length n.
        
        n: Defines last n datapoints included in calculation series. Integer.
        prices: Column name from dataframe on which to perform calculation. String. Typicaly 'Close'.
        """
        #Iskanje highest-high in lowest-low v seriji podatkov
        df = pd.Series(self.data[price], name="nw").to_frame()
        #Maximum
        max_peaks_idx = df.nw.rolling(window=n).apply(lambda x: x.argmax()).fillna(0).astype(int)
        df['max_peaks_idx'] = pd.Series(max_peaks_idx).to_frame()
        df['max_peaks_nw'] = pd.Series(df.nw.iloc[max_peaks_idx.values].values, index=df.nw.index)
        #Minimum
        min_peaks_idx = df.nw.rolling(window=n).apply(lambda x: x.argmin()).fillna(0).astype(int)
        df['min_peaks_idx'] = pd.Series(min_peaks_idx).to_frame()
        df['min_peaks_nw'] = pd.Series(df.nw.iloc[min_peaks_idx.values].values, index=df.nw.index)
        #Counts
        num_max_values_1 = [0 for i in range(n)]
        num_min_values_1 = [0 for i in range(n)]

        num_max_values_2 = [len(set(list(df['max_peaks_nw'])[i:(i+n)])) for i in range(n, len(list(df['max_peaks_idx'])))]
        num_min_values_2 = [len(set(list(df['min_peaks_nw'])[i:(i+n)])) for i in range(n, len(list(df['min_peaks_idx'])))]
        self.data['num_max_values'] = num_max_values_1 + num_max_values_2
        self.data['num_min_values'] = num_min_values_1 + num_min_values_2
        
        return
    
    def num_peaks_diff(self, n=6, price = 'Close'):
        """
        Custom indicator. Updated num_peaks. It devides the number of lowest lows from highest highs in a series, returns a single "value" that oscilates around 0.

        n: Defines last n datapoints included in calculation series. Integer.
        prices: Column name from dataframe on which to perform calculation. String. Typicaly 'Close'.
        """
        
        self.num_peaks(n, price)
        
        self.data['num_peaks_diff'] = self.data.apply(lambda x: x['num_max_values'] - x['num_min_values'], axis=1)
        
        return
    
    def save_csv(self, file_name):
        """file_name: Define name for save. End with .csv (Example: 'January2022.csv')."""
        self.data.to_csv(file_name, encoding='utf-8', index=False)
        return
        
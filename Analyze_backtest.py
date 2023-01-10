# Version 1.3
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
from Visualize_data import Visualize_data

class Analyze_backtest(): #Analyzes the results of the Trade_logic methods.
    def __init__(self, dataframe, cash=100, fee=0.995):
        """
        dataframe: Pandas dataframe, result from calling Harvest_data.get_data() and then Trade_logic methods
        cash: Amount of initial "cash" with which to trade. Integer. Default 100 (ticker2 units)
        fee: Float. Fee amount of each transaction (binance 0.1% = 0.999). To also account for slippage when making trades I have put it at 0.995.
        """
        self.data = dataframe
        self.cash = cash
        self.fee = fee
    
    def MDD(self, acc_value):
        """
        Calculates MDD (Maximum Drawdown).

        acc_value: List. Value of account at each time point.
        """
        df = pd.Series(acc_value, name="nw").to_frame()
        max_peaks_idx = df.nw.expanding(min_periods=1).apply(lambda x: x.argmax()).fillna(0).astype(int)
        df['max_peaks_idx'] = pd.Series(max_peaks_idx).to_frame()

        nw_peaks = pd.Series(df.nw.iloc[max_peaks_idx.values].values, index=df.nw.index)

        df['dd'] = ((df.nw-nw_peaks)/nw_peaks)
        df['mdd'] = df.groupby('max_peaks_idx').dd.apply(lambda x: x.expanding(min_periods=1).apply(lambda y: y.min())).fillna(0)

        return min(list(df['mdd']))*100
    
    def win_loss_count(self, acc_value):
        """
        Counts the the number of win vs. loss trades. Returns number of wins, losses and average win and loss size.

        acc_value: List. Value of account at each time point.
        """
        win = 0
        loss = 0
        win_size = []
        loss_size = []
        for i in range(1, len(acc_value)):
            if acc_value[i-1] < acc_value[i]:
                win +=1
                win_size.append(acc_value[i] - acc_value[i-1])
            elif acc_value[i-1] > acc_value[i]:
                loss += 1
                loss_size.append(acc_value[i] - acc_value[i-1])
                
        avg_win = np.mean(win_size)
        avg_loss = np.mean(loss_size)
        return win, loss, avg_win, avg_loss
    
    def calculate_trades(self, trades_col, price_col='Close'):
        """
        Calculates trades based on trade signals provided by Trade_logic methods.

        trades_col: String. Name of column with BUY/SELL signals.
        price_col: String. Name of column with prices.
        """
        trades = list(self.data[trades_col])
        price = list(self.data[price_col])
        
        #Calculates account value after each BUY -> SELL. Always trades with 100% of account value.
        cash = self.cash
        crypto = 0
        value = [cash]
        state = 'cash'
        
        for i in range(len(trades)):
            if trades[i] == 'BUY':
                crypto = value[i] * (1/price[i]) * self.fee
                value.append(value[i])
                state = 'crypto'
            elif trades[i] == 'SELL':
                cash = crypto * price[i] * self.fee
                value.append(cash)
                state = 'cash'
            else:
                if state == 'cash':
                    value.append(value[i])
                elif state == 'crypto':
                    value.append(crypto * price[i] * self.fee)
        return value
    
    def analyze(self, enable_log=False): 
        
        hodl = self.calculate_trades('Trades-BnH') #Calculates buy and hold account value for comparison
        value = self.calculate_trades(self.data.columns[-1]) #Takes last column with trade signals from Trade_logic methods
            
        self.data['Buy and Hold value'] = hodl[1:]
        self.data['Value'] = value[1:]
        
        wins, losses, avg_win, avg_loss = self.win_loss_count(value)
        
        log = {'value_series': value, 'Account value:':value[-1], 'Account value with buy and hold:': hodl[-1], 'Number of trades:': (len(list(self.data.loc[self.data[self.data.columns[-3]]=='SELL', 'Open']))), 'Total PnL:': ((((value[-1]-value[0])/value[0])*100)), 'Wins:': wins, 'Losses:': losses, 'Average win:': avg_win, 'Average loss:': avg_loss, 'Maximum Drawdown (MDD):': self.MDD(value)}
        
        if enable_log == True: # Returns dict with analysis results
            return log
        else:
            print('Account value:', value[-1])
            print('Account value with buy and hold:', "{:.2f}".format(hodl[-1]))
            print('Total PnL:', "{:.2f}".format(((value[-1]-value[0])/value[0])*100),'%')
            print('Number of trades:', len(list(self.data.loc[self.data[self.data.columns[-3]]=='SELL', 'Open'])))
            print('Wins:', wins)
            print('Losses:', losses)
            try:
                print('Win percentage:', "{:.2f}".format((wins/(wins+losses)*100)),'%') #Percentage of winning trades
            except:
                print('Win percentage: Error division by zero - no trades')
            print('Average win:', "{:.2f}".format(avg_win))
            print('Average loss:', "{:.2f}".format(avg_loss)) 
            print('Maximum Drawdown (MDD):', "{:.2f}".format((self.MDD(value))),'%')
        
            fig = Visualize_data(self.data)
            return fig.simple_visualize('Value', 'Buy and Hold value')
    

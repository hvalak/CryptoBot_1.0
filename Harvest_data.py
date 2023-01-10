#Version 1.3
import config
import requests
import pandas as pd
from datetime import datetime

class Harvest_data(): #Gather historical data for a selected period
    
    def __init__(self, ticker1, ticker2, start_date, end_date='now', interval = '1m'):
        """
        ticker1, ticker2: Trading pair. Example: 'ETH' and 'EUR' --> 'ETHEUR'
        start_date: Data start date. String format: 'yyyy-mm-dd'. Example: '2022-02-26'
        end_date: Data end date. Same as start_date. If left empty it takes last "full" day (yesterday midnight). Last date included (same as [1:5] 5 is not in).
        interval: Data time interval. Possible: '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w'
        """
        self.ticker1 = ticker1
        self.ticker2 = ticker2
        self.pair = ticker1 + ticker2
        self.start_date = int(datetime.timestamp(datetime.strptime(start_date, '%Y-%m-%d')) * 1000)
        
        if end_date == 'now':
            self.end_date = int(datetime.timestamp(datetime.now())*1000)
        else:
            self.end_date = int(datetime.timestamp(datetime.strptime(end_date, '%Y-%m-%d')) * 1000)
       
        self.interval = interval
        
    
    def get_data(self):
        """
        Collects data by calling binance API for historical data.
        """
        k = {'1m':60000, '3m':180000, '5m':300000, '15m':900000, '30m':1800000, '1h':3600000, '2h':7200000, '4h':14400000, '6h':21600000, '8h':28800000, '12h':43200000, '1d':86400000, '3d':259200000,'1w':604800000}
        limit = 1000
        time = [[self.start_date, limit]]
        
        #Binance API gives max. 1000 entries per API call, if more datapoints are needed it makes several calls and joins data

        num = int((self.end_date - self.start_date) / (1000 * k[self.interval]))
        ostanek = int((self.end_date - (self.start_date + num * 1000 * k[self.interval])) / k[self.interval])
        
        if num > 0:
            for i in range(num):
                a = 1000 * k[self.interval]
                time.append([time[-1][0] + a, limit])
                if (self.end_date - time[-1][0]) < (1000 * k[self.interval]):
                    time[-1][1] = ostanek
                else:
                    pass
        else:
            time[-1][1] = ostanek
        
        data = []
        
        base_url = 'https://api.binance.com'
        headers = {'X-MBX-APIKEY': config.API_KEY}
        end_url = '/api/v1/klines'
        
        for chunk in time:
            params = {
                'symbol': self.pair,
                'interval': self.interval,   
                'limit': chunk[1],
                'startTime': chunk[0],      
            }

            url = base_url + end_url
            r = requests.get(url, headers=headers, params=params)
            dat = r.json()
            for kline in dat:
                    data.append(kline)

        self.data = pd.DataFrame(data, columns = ['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        
        #Dataframe with binance historical data, for Open and Close times converts unix time to "human friendly" time string
        self.data['Open date'] = [datetime.strftime(y, "%m/%d/%Y, %H:%M:%S") for y in [datetime.fromtimestamp(x) for x in ((self.data['Open time'] / 1000).astype('int'))]]
        self.data['Close date'] = [datetime.strftime(y, "%m/%d/%Y, %H:%M:%S") for y in [datetime.fromtimestamp(x) for x in ((self.data['Close time'] / 1000).astype('int'))]]
        
        return
    
    def save_csv(self, file_name):
        """
        Saves dataframe with historical data as .csv file

        file_name: Define file name. String ending with .csv (Example: 'ETH_January2022.csv').
        """
        self.data.to_csv(file_name, encoding='utf-8', index=False)
        return
    
    def save_pickle(self, file_name):
        """
        Saves dataframe with historical data as .pkl pandas file

        file_name: Define file name. String ending with .pkl (Example: 'ETH_January2022.pkl').
        """
        self.data.to_pickle(file_name)
        return
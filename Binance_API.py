# Verzija 1.1

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests
from discord import Webhook, RequestsWebhookAdapter

class Binance_API(): #Zbirka metod za klicanje binance API-ja za info in kreiranje order-jev
    
    def __init__(self,  ticker1, ticker2, testnet=False, log_path='log_default.csv', discord_webhook_url = ''):
        """
        Class v katerem so združene različne metode za klic binance API-ja. Za Izvajanje Order-jev in informacije za/o njih.
        ticker1, ticker2: Skupaj tvorita trgovalni par. Primer: 'ETH' in 'EUR' tvorita 'ETHEUR'
        testnet: Z testnet=True pošiljamo ukaze na testno okolje. PAZI! Default vrednost je False (komunikacija z dejanskim binance računom!)
        log_path: string, ime datoteke kamor se zapisuje log po izvedbi orderja
        """
        self.ticker1 = ticker1
        self.ticker2 = ticker2
        self.pair = ticker1 + ticker2
        self.log_path = log_path
        self.discord_webhook_url = discord_webhook_url
      
        if testnet == False:
            from config import API_KEY, API_SECRET #V datoteki config.py sta zapisana API_KEY in API_SECRET z uvozom sta dosegljiva  notri
            self.API_KEY = API_KEY
            self.API_SECRET = API_SECRET
            self.base_url = 'https://api.binance.com'
        elif testnet == True:
            from config_testnet import API_KEY, API_SECRET#V datoteki config_testnet.py sta zapisana Testnet API_KEY in API_SECRET
            self.API_KEY = API_KEY
            self.API_SECRET = API_SECRET
            self.base_url = 'https://testnet.binance.vision' #Testnet naslov
        else:
            print('testnet mora biti True ali False!!!')
        
        self.headers = {'X-MBX-APIKEY': self.API_KEY}
        
        return

    def round_down(self, x, precision):
        return round(x - 5 * (10 ** (-precision - 1)), precision)
        
    def get_exchange_info(self):
        """
        Pridobi pravila o trgovalnem paru. Natančnost (decimalke), minimalna količina...
        """
        end_url = '/api/v3/exchangeInfo'

        params = {
            'symbol': self.pair,
        }

        url = self.base_url + end_url

        r = requests.get(url, headers=self.headers, params=params)
        data = r.json()
        
        #Pravila trgovanja (LOT_SIZE - previla o količini in natančnosti (decimalk) assetov za trgovanje)
        try:
            lot = pd.DataFrame(data['symbols'])
            lot = lot.set_index('symbol')
            lot = pd.DataFrame(lot.loc[self.pair, 'filters'])
            lot = lot.set_index('filterType').astype('float')
            self.min_lot_size = lot.loc['LOT_SIZE', 'minQty']
            step_size = lot.loc['LOT_SIZE', 'stepSize']
            self.precision = int(abs(np.log10(step_size)))
        except:
            raise ValueError('Vnešen neobstoječ trgovalni par. Message: ' + str(data))

        return
        
        
    def get_order_book(self, depth=5):
        """
        Vrne order book bid in ask-ov.
        depth: koliko bid/ask-ov vrne
        """
        end_url = '/api/v1/depth'

        params = {
            'symbol': self.pair,
            'limit': depth
        }

        url = self.base_url + end_url

        r = requests.get(url, headers=self.headers, params=params)
        data = r.json()
        return data

    def get_account_balance(self):
        """
        Vrne podatke o računu vezanem na api key in secret.
        """
        end_url = '/api/v3/account'
        timestamp = int(time.time() * 1000)
        params = {
            'recvWindow': 5000, #Če ni odgovora v 5s ptem ta ukaz propade
            'timestamp': timestamp
        }

        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        url = self.base_url + end_url
        r = requests.get(url, headers=self.headers, params=params)
        data = r.json()
        return data
    
    def get_open_orders(self):
        """
        Vrne podatke o vseh trenutno odprtih pozicijah (za trgovalni par).
        
        Če ni odprtih pozicij vrne [] (prazen list). Za preverjanje ali je list prazen uporabi:
        if not data:
            print('Ni odprtih pozicij')
        else:
            print('So odprte pozicije')
            
        Prazen list se v logični operaciji evalvira kot False.
        """
        end_url = '/api/v3/openOrders'
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': self.pair,
            'recvWindow': 5000, #Če ni odgovora v 5s ptem ta ukaz propade
            'timestamp': timestamp
        }

        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        url = self.base_url + end_url
        r = requests.get(url, headers=self.headers, params=params)
        data = r.json()
        return data
    
    def cancel_all_open_orders(self):
        """
        Zapre vse trenutno odprte pozicije za trgovalni par.
        """
        end_url = '/api/v3/openOrders'
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': self.pair,
            'recvWindow': 5000, #Če ni odgovora v 5s ptem ta ukaz propade
            'timestamp': timestamp
        }

        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        url = self.base_url + end_url
        r = requests.delete(url, headers=self.headers, params=params)
        data = r.json()
        return data
    
    def post_order(self, side, orderType='limit', timeInForce='GTC', percent=1.0, orderBookDepth=5):
        """
        Pošlje ukaz za nakup/prodajo.
        side: 'SELL' ali 'BUY', prodaja ali nakup
        orderType: Tip order-ja 'limit' ali 'market'
        timeInForce: Določi trajanje veljavnosti naročila: GTC (Good-Till-Cancel) - velja dokler ni zapolnjen ali dobi ukaz za prekinitev
                                                           IOC (Immediate-Or-Cancel) - Zapolnjen takoj po limit ceni nato zavržen, lahko je delno zapolnjen
                                                           FOK (Fill-Or-Kill) - Popolnoma zapolnjen takoj ali zavržen.
        percent: Določi delež vrednosti naročila od celotne vrednosti na accountu. PAZI BUY stran: Če fee plačaš z BNB je lahko 100%, Drugače moraš upoštevati fee-je in potencialni slippage. Na forumu priporočajo 0.999.
        orderBookDepth: Določi koliko bidov in askov dobimo iz klica get_order_book. Povečati za večje vsote, default je 5.
        """
        #price izračun
        orderBook = self.get_order_book(depth = orderBookDepth)
        if side == 'SELL':
            pass #Cena je določena ko preveri ali je prvi bid dovolj velik da zapolne naročilo
        elif side == 'BUY':
            price = float(orderBook['asks'][0][0])
        else:
            print('side mora biti BUY ali SELL!!!')
        
        #quantity izračun
        accountBalance = self.get_account_balance()
        balances = pd.DataFrame(accountBalance['balances'])
        balances = balances.set_index('asset').astype('float')
                  
        if side == 'SELL':
            tickerBalance = balances.loc[self.ticker1, 'free']
            quantity = tickerBalance * percent
            quantity = self.round_down(quantity, self.precision)
        elif side == 'BUY':
            tickerBalance = balances.loc[self.ticker2, 'free']
            quantity = tickerBalance * (1 / price) * percent
            quantity = self.round_down(quantity, self.precision) #nastavi da bo precision ustrezal koraku trgovanja LOT_SIZE, zaokroži DOL
            
        #Preračun price, da bo za quantity takoj zapolnjen (filled) zahtevek (order)
        bids = pd.DataFrame(orderBook['bids'], columns=['price', 'quantity']).astype('float')
        asks = pd.DataFrame(orderBook['asks'], columns=['price', 'quantity']).astype('float')
        
        if side == 'SELL':
            bids['cumsum']=bids['quantity'].cumsum()
            for i in range(len(bids['cumsum'])):
                if quantity <= bids['cumsum'][i]: #Če orderji pogosto ne bodo takoj zapolnjeni tukaj nastavi samo <
                    price = bids['price'][i]
                    break
                else:
                    pass
        elif side == 'BUY':
            asks['cumsum']=asks['quantity'].cumsum()
            for i in range(len(asks['cumsum'])):
                if quantity <= asks['cumsum'][i]: #Če orderji pogosto ne bodo takoj zapolnjeni tukaj nastavi samo <
                    price = asks['price'][i]
                    quantity = tickerBalance * (1 / price) * percent
                    quantity = self.round_down(quantity, self.precision)
                    break
                else:
                    pass
        
        #API klic    
        end_url = '/api/v3/order'
        timestamp = int(time.time() * 1000)
        params = {
            'symbol': self.pair,
            'side': side,
            'type': orderType,
            'timeInForce': timeInForce,
            'quantity': quantity,
            'price': price,
            'recvWindow': 5000,
            'timestamp': timestamp
        }

        query_string = urlencode(params)
        params['signature'] = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        url = self.base_url + end_url
        r = requests.post(url, headers=self.headers, params=params)
        data = r.json()
        return data
    
    def send_discord_notification(self, data):
        """
        Na Discord pošlje podatke o izvedeni transakciji.
        data: rezultat klica funkcije order
        """
        webhook = Webhook.from_url(self.discord_webhook_url, adapter=RequestsWebhookAdapter())
        
        try:
            if data['side'] == 'BUY':
                webhook.send(
                    '** IZVEDENA TRANSAKCIJA! **' + '\n'
                    'Datum: '+ datetime.strftime(datetime.fromtimestamp((int(data['transactTime'] / 1000))), "%m/%d/%Y %H:%M:%S") + '\n'
                    'Simbol: '+ data['symbol'] + '\n'
                    'Side: '+ data['side'] + '\n'
                    'Po ceni: '+ data['price'] + ' ' + self.ticker2 + '/' + self.ticker1 + '\n'
                    'Kupljena količina : '+ data['executedQty'] + ' ' + self.ticker1 + '\n'
                    'Status: '+ data['status'] + '\n'
                    'fills: '+ str(data['fills']) + '\n'
                    '################################')
            elif data['side'] == 'SELL':
                webhook.send(
                    '** IZVEDENA TRANSAKCIJA! **' + '\n'
                    'Datum: '+ datetime.strftime(datetime.fromtimestamp((int(data['transactTime'] / 1000))), "%m/%d/%Y %H:%M:%S") + '\n'
                    'Simbol: '+ data['symbol'] + '\n'
                    'Side: '+ data['side'] + '\n'
                    'Po ceni: '+ data['price'] + ' ' + self.ticker2 + '/' + self.ticker1 + '\n'
                    'Kupljena količina : '+ data['executedQty'] + ' ' + self.ticker2 + '\n'
                    'Status: '+ data['status'] + '\n'
                    'fills: '+ str(data['fills']) + '\n'
                    '################################')
            return
        except:
            webhook.send(
                'Nekaj ni vredu! Beri:'
                '' + str(data) + '')
    
    def log(self, data):
        """
        Piše log.
        data: 
        """
        log_df = pd.DataFrame(data)
        log_df.to_csv(self.log_path, mode='a', header=False) #mode= 'a' pomeni da apenda novo vrstico
        

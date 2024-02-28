from binanceUtils import BinanceEnvVars
from binance.client import Client
from binance.enums import *

class Binance:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret)

    def get_funding_rates(self, symbols: list):
        funding_rates = []
        for symbol in symbols:
            try:
                futures_funding_rate = self.client.futures_funding_rate(symbol=symbol)
                if futures_funding_rate and len(futures_funding_rate) > 0:
                    latest_rate = futures_funding_rate[-1]
                    funding_rates.append({
                        'market_name': symbol,
                        'funding_rate': latest_rate.get('fundingRate'),
                    })
            except Exception as e:
                print(f"Error fetching funding rate for {symbol}: {e}")
        return funding_rates

binance = Binance()
symbols = ['BTCUSDT', 'ETHUSDT']
funding_rates = binance.get_funding_rates(symbols)
print(funding_rates)

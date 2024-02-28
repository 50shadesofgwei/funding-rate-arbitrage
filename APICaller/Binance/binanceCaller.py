from APICaller.Binance.binanceUtils import BinanceEnvVars
from binance.client import Client
from binance.enums import *

class BinanceCaller:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret)

    def _fetch_funding_rate_for_symbol(self, symbol: str):
        try:
            futures_funding_rate = self.client.futures_funding_rate(symbol=symbol)
            if futures_funding_rate and len(futures_funding_rate) > 0:
                return futures_funding_rate[-1]
        except Exception as e:
            print(f"Error fetching funding rate for {symbol}: {e}")
        return None

    def _parse_funding_rate_data(self, funding_rate_data, symbol: str):
        if funding_rate_data:
            return {
                'exchange': 'Binance',
                'symbol': symbol,
                'funding_rate': funding_rate_data.get('fundingRate'),
            }
        else:
            return None

    def get_funding_rates(self, symbols: list):
        funding_rates = []
        for symbol in symbols:
            funding_rate_data = self._fetch_funding_rate_for_symbol(symbol)
            parsed_data = self._parse_funding_rate_data(funding_rate_data, symbol)
            if parsed_data:
                funding_rates.append(parsed_data)
        return funding_rates

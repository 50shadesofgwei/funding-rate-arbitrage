from APICaller.Binance.binanceUtils import BinanceEnvVars
from GlobalUtils.logger import *
from binance.um_futures import UMFutures as Client
from binance.enums import *

from dotenv import load_dotenv

load_dotenv()

class BinanceCaller:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret)

    def get_price(self, symbol: str) -> float:
        try:
            response = self.client.mark_price(symbol=symbol)
            if 'markPrice' not in response:
                raise KeyError("markPrice key not found in the response.")
            
            price = float(response['markPrice'])
            return price
        except KeyError as e:
            logger.info(f"BinanceAPICaller - Error: {e}. Unable to find required data in the response for symbol {symbol}.")
        except ValueError as e:
            logger.info(f"BinanceAPICaller - Error converting price to float for symbol {symbol}: {e}. Check response format.")
        except Exception as e:
            logger.info(f"BinanceAPICaller - An error occurred while fetching the mark price for {symbol}: {e}.")
        return None

    def get_funding_rates(self, symbols: list):
        funding_rates = []
        try:
            for symbol in symbols:
                funding_rate_data = self._fetch_funding_rate_for_symbol(symbol)
                parsed_data = self._parse_funding_rate_data(funding_rate_data, symbol)
                if parsed_data:
                    funding_rates.append(parsed_data)
            return funding_rates
        except Exception as e:
            logger.error(f"BinanceAPICaller - Failed to fetch or parse funding rates for symbols. Error: {e}")
            return None

    def get_historical_funding_rate_for_symbol(self, symbol: str, limit: int) -> list:
        try:
            response = self.client.funding_rate(symbol=symbol, limit=limit)
            return response
        except Exception as e:
            logger.error(f'BinanceAPICaller - Error while calling historical rates for symbol {symbol}, limit: {limit}, {e}')
            return None
    
    def _fetch_funding_rate_for_symbol(self, symbol: str):
        try:
            futures_funding_rate = self.client.funding_rate(symbol=symbol)
            if futures_funding_rate and len(futures_funding_rate) > 0:
                return futures_funding_rate[-1]
        except Exception as e:
            logger.error(f"BinanceAPICaller - Error fetching funding rate for {symbol}: {e}")
        return None
        
    def _parse_funding_rate_data(self, funding_rate_data, symbol: str):
        if funding_rate_data:
            rate_as_float = float(funding_rate_data.get('fundingRate'))
            return {
                'exchange': 'Binance',
                'symbol': symbol,
                'funding_rate': rate_as_float,
            }
        else:
            logger.error(f"BinanceAPICaller - No funding rate data available for symbol: {symbol}")
            return None


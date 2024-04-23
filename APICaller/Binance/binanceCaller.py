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
        except Exception as e:
            logger.error(f"BinanceAPICaller - Failed to fetch or parse funding rates for symbols. Error: {e}")
        return funding_rates

    def calculate_skew_impact(symbol, trade_size_contracts):
        """
        Estimate the impact of a trade on the market's skew and funding rate.
        
        Args:
        symbol (str): The market symbol (e.g., 'BTCUSDT').
        trade_size_contracts (int): The size of the trade in contracts.
        
        Returns:
        float: The estimated impact on the funding rate skew.
        """

    def get_historical_funding_rate_for_symbol(self, symbol: str, limit: int) -> list:
        response = self.client.funding_rate(symbol=symbol, limit=limit)
        return response


    def calculate_skew_impact_per_hundred_dollars(symbol, dollar_trade_size):
        """Calculate the skew impact per $100 of contracts."""
    
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
            return {
                'exchange': 'Binance',
                'symbol': symbol,
                'funding_rate': funding_rate_data.get('fundingRate'),
            }
        else:
            logger.info(f"BinanceAPICaller - No funding rate data available for symbol: {symbol}")
            return None


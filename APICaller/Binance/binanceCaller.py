import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.Binance.binanceUtils import BinanceEnvVars
from GlobalUtils.logger import *
from binance.um_futures import UMFutures as Client
from binance.enums import *
import os
from dotenv import load_dotenv

load_dotenv()

class BinanceCaller:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret, base_url="https://testnet.binancefuture.com")

    @log_function_call
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

    @log_function_call
    def _fetch_funding_rate_for_symbol(self, symbol: str):
        try:
            futures_funding_rate = self.client.funding_rate(symbol=symbol)
            if futures_funding_rate and len(futures_funding_rate) > 0:
                return futures_funding_rate[-1]
        except Exception as e:
            logger.error(f"BinanceAPICaller - Error fetching funding rate for {symbol}: {e}")
        return None

    @log_function_call
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
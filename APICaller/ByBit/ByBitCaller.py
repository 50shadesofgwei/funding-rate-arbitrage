from pybit.unified_trading import HTTP
from APICaller.ByBit.ByBitUtils import *
from GlobalUtils.logger import logger

class ByBitCaller:
    def __init__(self):
        self.client = get_ByBit_client()

    def _fetch_funding_rate_data(self, symbol: str):
        try:
            response = self.client.get_funding_rate_history(
                category='linear',
                symbol=symbol,
                limit='1',
                fundingInterval='1'
            )
            if response.get('retCode') == 0:
                return response
            else:
                logger.error(f"ByBitAPICaller - funding rate API Error for {symbol}: {response.get('retMsg')}")
        except Exception as e:
            logger.error(f"ByBitAPICaller - Failed to fetch funding rate data for {symbol}: {e}")
            return None

    def _parse_funding_rate_data(self, data, symbol: str):
        try:
            if data and 'result' in data and 'list' in data['result'] and len(data['result']['list']) > 0:
                funding_rate_info = data['result']['list'][0]
                return {
                    'exchange': 'ByBit',
                    'symbol': symbol,
                    'funding_rate': funding_rate_info.get('fundingRate'),
                }
            else:
                logger.info(f"ByBitAPICaller - No funding rate data available for {symbol}.")
                return None
        except Exception as e:
            logger.error(f"ByBitAPICaller - Error parsing funding rate data for {symbol}: {e}")
            return None

    def get_funding_rates(self, symbols: list):
        funding_rates = []
        try:
            for symbol in symbols:
                data = self._fetch_funding_rate_data(symbol)
                if data:
                    funding_rate_info = self._parse_funding_rate_data(data, symbol)
                    if funding_rate_info:
                        funding_rates.append(funding_rate_info)
                    else:
                        logger.error(f"ByBitAPICaller - Failed to parse funding rate data for {symbol} from ByBit API.")
                else:
                    logger.error(f"ByBitAPICaller - Failed to fetch funding rate data for {symbol} from ByBit API.")
            return funding_rates
        except Exception as e:
            logger.error(f"ByBitAPICaller - Error getting funding rates for symbols: {e}")
            return funding_rates



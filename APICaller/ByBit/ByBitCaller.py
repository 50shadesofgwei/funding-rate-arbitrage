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
                raise ValueError(f"API Error for {symbol}: {response.get('retMsg')}")
        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch funding rate data for {symbol} from API: {e}")
            return None

    def _parse_funding_rate_data(self, data, symbol: str):
        if data:
            return {
                'market_name': symbol,
                'funding_rate': data['result']['list'][0]['fundingRate'],
            }

    def get_funding_rate_for_symbol(self, symbol: str):
        data = self._fetch_funding_rate_data(symbol)
        if data:
            funding_rate_info = self._parse_funding_rate_data(data, symbol)
            if funding_rate_info:
                print(funding_rate_info)
                return funding_rate_info
            else:
                logger.error(f"ByBitCaller - Failed to parse funding rate data for {symbol} from ByBit API.")
                return None
        else:
            logger.error(f"ByBitCaller - Failed to fetch funding rate data for {symbol} from ByBit API.")
            return None

    def get_historical_funding_rate_for_symbol(self, symbol: str) -> list:
        try:
            response = self.client.get_funding_rate_history(
                category='linear',
                symbol=symbol,
                limit='200',
            )
            if response.get('retCode') == 0:
                return response
            else:
                raise ValueError(f"ByBitCaller - API Error while calling historical funding rate for {symbol}: {response.get('retMsg')}")
        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch funding rate data for {symbol} from API: {e}")
            return None

    def get_funding_rates(self, symbols: list) -> list:
        funding_rates = []
        try:
            for symbol in symbols:
                funding_rate_data = self.get_funding_rate_for_symbol(symbol)
                parsed_data = self._parse_funding_rate_data(funding_rate_data, symbol)
                if parsed_data:
                    funding_rates.append(parsed_data)
        except Exception as e:
            logger.error(f"BinanceAPICaller - Failed to fetch or parse funding rates for symbols. Error: {e}")
        return funding_rates

# x = ByBitCaller()
# y = x.get_funding_rate_for_symbol('ETHUSDT')
# print(y)
from APICaller.ByBit.ByBitUtils import *
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import normalize_funding_rate_to_8hrs

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

    def _parse_funding_rate_data(self, data: dict, symbol: str):
        try:
            if data:
                return {
                    'exchange': 'ByBit',
                    'market_name': symbol,
                    'funding_rate': data['result']['list'][0]['fundingRate'],
                }
        except Exception as e:
            logger.error(f'ByBitCaller - Error while parsing funding rate data. Data={data}, symbol={symbol}. Error: {e}')
            return None

    def get_funding_rate_for_symbol(self, symbol: str):
        data = self._fetch_funding_rate_data(symbol)
        interval = self.get_funding_interval_for_symbol(symbol)
        if data:
            funding_rate_info = self._parse_funding_rate_data(data, symbol)
            rate = float(funding_rate_info['funding_rate'])
            normalized_rate = normalize_funding_rate_to_8hrs(rate, interval)
            funding_rate_info['funding_rate'] = normalized_rate
            if funding_rate_info:
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
                if funding_rate_data:
                    funding_rates.append(funding_rate_data)

            return funding_rates
        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch or parse funding rates for symbols. Error: {e}")
            return None

    def get_funding_interval_for_symbol(self, symbol: str) -> int:
        try:
            response = self.client.get_instruments_info(
                category='linear',
                symbol=symbol
                )
            if response.get('retCode') == 0:
                funding_interval_mins: int = response['result']['list'][0]['fundingInterval']
                funding_interval_hours = funding_interval_mins / 60
                return funding_interval_hours

        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch or parse funding interval for symbol {symbol}. Error: {e}")
            return None

from APICaller.ByBit.ByBitUtils import *
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *

class ByBitCaller:
    def __init__(self):
        self.client = GLOBAL_BYBIT_CLIENT

    def _fetch_funding_rate_data(self, symbol: str):
        try:
            response = self.client.get_tickers(
                category='linear',
                symbol=symbol,
                limit='1',
                fundingInterval='1'
            )
            if response.get('retCode') == 0 or '0':
                return response
            else:
                return None
        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch funding rate data for {symbol} from API. Error: {e}")
            return None

    def _parse_funding_rate_data(self, data: dict, symbol: str) -> dict:
        try:
            if data and data.get('retCode') == 0 and 'result' in data and 'list' in data['result']:
                return {
                    'exchange': 'ByBit',
                    'symbol': symbol,
                    'funding_rate': data['result']['list'][0]['fundingRate'],
                }
        except Exception as e:
            logger.error(f'ByBitCaller - Error while parsing funding rate data. Data={data}, symbol={symbol}. Error: {e}')
        return None


    def get_funding_rate_for_symbol(self, symbol: str) -> dict:
        try:
            data = self._fetch_funding_rate_data(symbol)
            if not data:
                return None
            price = float(data['result']['list'][0]['indexPrice'])
            interval = self.get_funding_interval_for_symbol(symbol)
            if data:
                funding_rate_info = self._parse_funding_rate_data(data, symbol)
                rate = float(funding_rate_info['funding_rate'])
                normalized_rate = normalize_funding_rate_to_8hrs(rate, interval)
                funding_rate_info['funding_rate'] = normalized_rate
                skew = self.get_skew(symbol, price)
                funding_rate_info['skew_usd'] = skew

                if funding_rate_info:
                    return funding_rate_info
                else:
                    logger.error(f"ByBitCaller - Failed to parse funding rate data for {symbol} from ByBit API.")
                    return None

        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch funding rate data for {symbol} from ByBit API. Error: {e}")
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
                else:
                    continue

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

            elif response == None:
                logger.error(f"ByBitCaller - None response while calling funding interval from API, symbol: {symbol}. Error: {e}")
                return None

        except Exception as e:
            logger.error(f"ByBitCaller - Failed to fetch or parse funding interval for symbol {symbol}. Error: {e}")
            return None

    def get_skew(self, symbol: str, price: float) -> float:
        try:
            response = self.client.get_open_interest(
                category='linear', 
                symbol=symbol,
                intervalTime="5min")
            if response and response.get('retCode') == 0 and 'result' in response and 'list' in response['result']:
                open_interest_list = response['result']['list']
                skew = float(open_interest_list[0]['openInterest'])
                skew_usd = skew * price
                return skew_usd
            
        except Exception as e:
            logger.error(f'ByBitCaller - Error while calculating skew for symbol={symbol}. Error: {e}')
            return None


    def get_next_funding_events_for_time_period(self, symbol: str, time_period_hours: int) -> int:
        try:
            interval = self.get_funding_interval_for_symbol(symbol)
            time_period_minutes = time_period_hours * 60
            response = self.client.get_tickers(
                category='linear', 
                symbol=symbol,
                intervalTime="5min"
            )

            if response and response.get('retCode') == 0 and 'result' in response and 'list' in response['result']:
                list = response['result']['list']
                next_funding_time = int(list[0]['nextFundingTime'])
                ms_to_next_funding_event = get_milliseconds_until_given_timestamp(next_funding_time)
                minutes_to_next_funding_event = ms_to_next_funding_event / 60000
                
                remaining_minutes = time_period_minutes - minutes_to_next_funding_event
                if remaining_minutes < 0:
                    return 0
                
                number_of_events = 1 + math.floor(remaining_minutes / (interval * 60))
                return number_of_events

        except Exception as e:
            logger.error(f'ByBitCaller - Error while calculating funding events for symbol={symbol}. Error: {e}')
            return None
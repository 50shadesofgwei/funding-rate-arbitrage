from pybit.unified_trading import HTTP
from ByBitUtils import *

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
            print(f"Failed to fetch funding rate data for {symbol} from ByBit API: {e}")
            return None

    def _parse_funding_rate_data(self, data, symbol: str):
        if data and 'result' in data and 'list' in data['result'] and len(data['result']['list']) > 0:
            funding_rate_info = data['result']['list'][0]
            return {
                'exchange': 'ByBit',
                'symbol': symbol,
                'funding_rate': funding_rate_info.get('fundingRate'),
            }
        else:
            print(f"No funding rate data available for {symbol} from ByBit API.")
            return None

    def get_funding_rates(self, symbols: list):
        funding_rates = []
        for symbol in symbols:
            data = self._fetch_funding_rate_data(symbol)
            if data:
                funding_rate_info = self._parse_funding_rate_data(data, symbol)
                if funding_rate_info:
                    funding_rates.append(funding_rate_info)
                else:
                    print(f"Failed to parse funding rate data for {symbol} from ByBit API.")
            else:
                print(f"Failed to fetch funding rate data for {symbol} from ByBit API.")
        return funding_rates

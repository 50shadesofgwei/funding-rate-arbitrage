from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *

from dotenv import load_dotenv

load_dotenv()

class OKXCaller:
    # Rate limit: 5 requests per 2 seconds
    # Rate limit rule: IP + instrumentID
    def __init__(self):
        # self.okx_pub_client = GLOBAL_OKX_PUBLIC_CLIENT
        # self.okx_trading_data_client = GLOBAL_OKX_TRADING_DATA_CLIENT
        pass

    def get_price(self, symbol: str) -> float:
        try:
            response = self.okx_pub_client.get_mark_price(instId=symbol, instType = 'SWAP')
            if 'markPx' not in response['data'][0]:
                raise KeyError("markPrice key not found in the response.")
            
            price = float(response['data'][0]['markPx'])
            return price
        except KeyError as e:
            logger.info(f"OkxAPICaller - Error: {e}. Unable to find required data in the response for symbol {symbol}.")
        except ValueError as e:
            logger.info(f"OkxAPICaller - Error converting price to float for symbol {symbol}: {e}. Check response format.")
        except Exception as e:
            logger.info(f"OkxAPICaller - An error occurred while fetching the mark price for {symbol}: {e}.")
        return None

    def get_funding_rates(self, symbols: list):
        funding_rates = []
        try:
            for symbol in symbols:
                funding_rate_data = self._fetch_funding_rate_for_symbol(symbol)
                skew = self.get_skew(symbol)
                parsed_data = self._parse_funding_rate_data(funding_rate_data, symbol)
                parsed_data['skew'] = skew
                if parsed_data:
                    funding_rates.append(parsed_data)
            return funding_rates
        except Exception as e:
            logger.error(f"OkxAPICaller - Failed to fetch or parse funding rates for symbols. Error: {e}")
            return None

    def get_historical_funding_rate_for_symbol(self, symbol: str, limit: int) -> list:
        # current max limit is 100
        # fundingRate	fundingTime	instId	instType	method	realizedRate
        # 0	-0.0001022593563945	1719820800000	BTC-USD-SWAP	SWAP	current_period	-0.0001022593563945
        # 1	0.000127022413948	1719792000000	BTC-USD-SWAP	SWAP	current_period	0.000127022413948
        try:
            response = self.pubDataAPI.funding_rate_history(symbol=symbol, limit=limit)
            return response
        except Exception as e:
            logger.error(f'OkxAPICaller - Error while calling historical rates for symbol {symbol}, limit: {limit}, {e}')
            return None
    
    def _fetch_funding_rate_for_symbol(self, symbol: str):
        try:
            futures_funding_rate = self.okx_pub_client.get_funding_rate(instId=symbol)
            if futures_funding_rate and len(futures_funding_rate['data']) > 0:
                return float(futures_funding_rate['data'][0]['fundingRate'])
        except Exception as e:
            logger.error(f"OkxAPICaller - Error fetching funding rate for {symbol}: {e}")
        return None
        
    def _parse_funding_rate_data(self, funding_rate_data, symbol: str):
        if funding_rate_data:
            rate_as_float = float(funding_rate_data)
            ccy = symbol.split('-')[0]

            return {
                'exchange': 'Okx',
                'symbol': ccy,
                'funding_rate': rate_as_float,
            }
        else:
            logger.error(f"OkxAPICaller - No funding rate data available for symbol: {symbol}")
            return None

    def get_skew(self, symbol: str) -> float:
        try:
            # long-short-account-ratio-contract in current OKX client is not supported
            open_interest_url = f"https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract?instId={symbol}"

            open_interest_response = requests.get(open_interest_url).json()
            ls_ratio = float(open_interest_response['data'][0][1])

            long_percent = ls_ratio / (1 + ls_ratio)
            short_percent = 1 / (1 + ls_ratio)

            ccy = symbol.split('-')[0]
            open_interest_response = self.okx_trading_data_client.get_contracts_interest_volume(ccy=ccy, period = '5m')
            open_interest_in_asset = float(open_interest_response['data'][0][1])

            amount_long = float(open_interest_in_asset * long_percent)
            amount_short = float(open_interest_in_asset * short_percent)
            skew = amount_long - amount_short
            return ls_ratio
        except Exception as e:
            logger.error(f'OkxAPICaller - Error while calculating skew for symbol {symbol}. Error: {e}')
            return None
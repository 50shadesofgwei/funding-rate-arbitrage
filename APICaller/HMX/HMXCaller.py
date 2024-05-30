from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

class HMXCaller:
    def __init__(self):
        self.client = GLOBAL_HMX_CLIENT

    def get_funding_rates(self, symbols) -> dict:
        try:
            all_market_data = self.client.public.get_all_market_info()
            funding_rates = self._filter_market_data(all_market_data=all_market_data, symbols=symbols)
            return funding_rates
        
        except Exception as e:
            logger.error(f'HMXCaller - Failed to get funding rates from API. Error: {e}')
            return None

    def _filter_market_data(self, all_market_data: dict, symbols: list) -> list:
        try:
            market_funding_rates = []
            market_entries = list(all_market_data.values())
            filtered_markets = [entry for entry in market_entries if entry['market'] in symbols]
            
            for market_data in filtered_markets:
                funding_rate_8H = market_data['funding_rate']['8H']
                market_price = market_data['price']
                borrowing_rate_8H = market_data['borrowing_rate']['8H']
                skew = float(market_data['long_size']) - float(market_data['short_size'])
                symbol = normalize_symbol(market_data['market'])
                    
                market_funding_rates.append({
                    'exchange': 'HMX',
                    'symbol': symbol,
                    'price': market_price,
                    'skew': skew,
                    'funding_rate': funding_rate_8H,
                    'borrowing_rate': borrowing_rate_8H
                })
            
            return market_funding_rates

        except Exception as e:
            logger.error(f"HMXCaller - Error processing market data for {market_data['market']}: {e}")
            return None

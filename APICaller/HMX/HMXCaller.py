from GlobalUtils.globalUtils import GLOBAL_HMX_CLIENT
from GlobalUtils.logger import logger
from APICaller.master.MasterUtils import get_target_tokens_for_HMX

class HMXCaller:
    def __init__(self):
        self.client = GLOBAL_HMX_CLIENT

    def get_funding_rates(self) -> dict:
        all_market_data = self.client.public.get_all_market_info()
        symbols = get_target_tokens_for_HMX()
        funding_rates = self._filter_market_data(all_market_data=all_market_data, symbols=symbols)
        return funding_rates

    def _filter_market_data(self, all_market_data: dict, symbols: list) -> list:
        market_funding_rates = []
        market_entries = list(all_market_data.values())
        filtered_markets = [entry for entry in market_entries if entry['market'] in symbols]
        
        for market_data in filtered_markets:
            try:
                funding_rate_8H = market_data['funding_rate']['8H']
                market_price = market_data['price']
                long_size = market_data['long_size']
                short_size = market_data['short_size']
                borrowing_rate_8H = market_data['borrowing_rate']['8H']
                
                market_funding_rates.append({
                    'market': market_data['market'],
                    'price': market_price,
                    'long_size': long_size,
                    'short_size': short_size,
                    '8H_funding_rate': funding_rate_8H,
                    '8H_borrowing_rate': borrowing_rate_8H
                })
            except KeyError as e:
                logger.error(f"HMXCaller - Error processing market data for {market_data['market']}: {e}")
        
        return market_funding_rates


x = HMXCaller()
y = x.get_funding_rates()
print(y)
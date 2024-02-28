from synthetix import *
from SynthetixUtils import *

class SynthetixCaller:
    def __init__(self):
        self.client = get_synthetix_client()

    def get_funding_rate(self):
        try:
            _, markets_by_name = self.client.perps.get_markets()
            return self._get_market_data_from_response(markets_by_name)
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return None

    def _get_market_data_from_response(self, markets_by_name):
        market_funding_rates = []
        for market_name, market_data in markets_by_name.items():
            try:
                funding_rate = market_data['current_funding_rate']
                market_funding_rates.append({
                    'market_name': market_name,
                    'funding_rate': funding_rate,
                })
            except KeyError as e:
                print(f"Error processing market data for {market_name}: {e}")
        return market_funding_rates

test = SynthetixCaller()
funding_rates = test.get_funding_rate()
if funding_rates is not None:
    print(funding_rates)
else:
    print("TEST: Failed to fetch funding rates.")


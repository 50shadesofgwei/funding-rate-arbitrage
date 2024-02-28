from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *

class SynthetixCaller:
    def __init__(self):
        self.client = get_synthetix_client()

    def get_funding_rates(self, symbols: list):
        try:
            _, markets_by_name = self.client.perps.get_markets()
            return self._filter_market_data(markets_by_name, symbols)
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return []

    def _filter_market_data(self, markets_by_name, symbols):
        market_funding_rates = []
        for symbol in symbols:
            if symbol in markets_by_name:
                try:
                    market_data = markets_by_name[symbol]
                    funding_rate = market_data['current_funding_rate']
                    market_funding_rates.append({
                        'exchange': 'Synthetix',
                        'symbol': symbol,
                        'funding_rate': funding_rate,
                    })
                except KeyError as e:
                    print(f"Error processing market data for {symbol}: {e}")
        return market_funding_rates


test = SynthetixCaller()
funding_rates = test.get_funding_rates()
if funding_rates is not None:
    print(funding_rates)
else:
    print("TEST: Failed to fetch funding rates.")


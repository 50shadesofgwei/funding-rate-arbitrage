import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.master.MasterCaller import MasterCaller
from MatchingEngineUtils import *
import json

class matchingEngine:
    def __init__(self):
        self.api_caller = MasterCaller()

    def find_arbitrage_opportunities_for_symbol(self, sorted_rates):
        """Identify arbitrage opportunities for a given symbol."""
        arbitrage_opportunities = []
        if len(sorted_rates) > 1:
            long_opportunity = sorted_rates[0]
            short_opportunity = sorted_rates[-1]
            if float(short_opportunity['funding_rate']) > float(long_opportunity['funding_rate']):
                arbitrage_opportunity = {
                    'long_exchange': long_opportunity['exchange'],
                    'short_exchange': short_opportunity['exchange'],
                    'symbol': normalize_symbol(long_opportunity['symbol']),
                    'long_funding_rate': long_opportunity['funding_rate'],
                    'short_funding_rate': short_opportunity['funding_rate'],
                    'funding_rate_differential': float(short_opportunity['funding_rate']) - float(long_opportunity['funding_rate'])
                }
                arbitrage_opportunities.append(arbitrage_opportunity)
        return arbitrage_opportunities

    def find_delta_neutral_arbitrage_opportunities(self, funding_rates):
        """Find delta-neutral arbitrage opportunities from a list of funding rates."""
        opportunities = []
        rates_by_symbol = group_by_symbol(funding_rates)
        for symbol, rates in rates_by_symbol.items():
            sorted_rates = sort_funding_rates_by_value(rates)
            opportunities.extend(self.find_arbitrage_opportunities_for_symbol(sorted_rates))
        return opportunities

funding_rates = [{'exchange': 'Synthetix', 'symbol': 'BTC', 'funding_rate': 0.001259963777771721}, {'exchange': 'Synthetix', 'symbol': 'ETH', 'funding_rate': 0.002199182045337673}, {'exchange': 'Binance', 'symbol': 'BTCUSDT', 'funding_rate': '0.00053538'}, {'exchange': 'Binance', 'symbol': 'ETHUSDT', 'funding_rate': '0.00043581'}, {'exchange': 'ByBit', 'symbol': 'BTCPERP', 'funding_rate': '0.00030484'}, {'exchange': 'ByBit', 'symbol': 'ETHPERP', 'funding_rate': '0.0001'}]
test = matchingEngine()
opportunities = test.find_delta_neutral_arbitrage_opportunities(funding_rates)
for opportunity in opportunities:
    print(opportunity)

with open('data.json', 'w') as file:
    json.dump(opportunities, file, indent=4)

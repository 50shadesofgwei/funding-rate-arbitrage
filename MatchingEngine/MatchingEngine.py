import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from MatchingEngine.MatchingEngineUtils import *
from GlobalUtils.logger import *

class matchingEngine:
    def __init__(self):
        pass

    @log_function_call
    def find_arbitrage_opportunities_for_symbol(self, sorted_rates):
        arbitrage_opportunities = []
        if len(sorted_rates) > 1:
            long_opportunity = sorted_rates[0]
            short_opportunity = sorted_rates[-1]
            long_rate = float(long_opportunity['funding_rate'])
            short_rate = float(short_opportunity['funding_rate'])
            if short_rate > long_rate:
                arbitrage_opportunity = {
                    'long_exchange': long_opportunity['exchange'],
                    'short_exchange': short_opportunity['exchange'],
                    'symbol': normalize_symbol(long_opportunity['symbol']),
                    'long_funding_rate': long_rate,
                    'short_funding_rate': short_rate,
                    'funding_rate_differential': short_rate - long_rate
                }
                arbitrage_opportunities.append(arbitrage_opportunity)
        return arbitrage_opportunities

    @log_function_call
    def find_delta_neutral_arbitrage_opportunities(self, funding_rates):
        opportunities = []
        rates_by_symbol = group_by_symbol(funding_rates)
        for symbol, rates in rates_by_symbol.items():
            sorted_rates = sort_funding_rates_by_value(rates)
            opportunities.extend(self.find_arbitrage_opportunities_for_symbol(sorted_rates))
        return opportunities




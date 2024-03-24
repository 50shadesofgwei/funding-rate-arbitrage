import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from MatchingEngine.MatchingEngineUtils import *
from GlobalUtils.logger import *

class matchingEngine:
    def __init__(self):
        pass

    @log_function_call
    def find_arbitrage_opportunities_for_symbol(self, sorted_rates):
        synthetix_opportunities = [rate for rate in sorted_rates if rate['exchange'] == 'Synthetix']
        
        arbitrage_opportunities = []
        for opportunity in synthetix_opportunities:
            funding_rate = float(opportunity['funding_rate'])
            
            if funding_rate > 0:
                long_exchange = 'Binance'
                short_exchange = 'Synthetix'
            else:
                # Shorts pay longs, so we want to be long on Synthetix (receiving) and short on Binance (hedging)
                long_exchange = 'Synthetix'
                short_exchange = 'Binance'

            arbitrage_opportunity = {
                'long_exchange': long_exchange,
                'short_exchange': short_exchange,
                'symbol': normalize_symbol(opportunity['symbol']),
                'funding_rate': funding_rate,  # Reflects Synthetix funding rate
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
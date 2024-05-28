from MatchingEngine.MatchingEngineUtils import *
from GlobalUtils.logger import *

class matchingEngine:
    def __init__(self):
        pass
    
    def find_arbitrage_opportunities_for_symbol(self, sorted_rates):
        try:
            rates_by_exchange = {}
            exchanges = set(rate['exchange'] for rate in sorted_rates)
            for exchange in exchanges:
                exchange_rates = [rate for rate in sorted_rates if rate['exchange'] == exchange]
                rates_by_exchange[exchange] = {normalize_symbol(rate['symbol']): rate for rate in exchange_rates}

            block_number = get_base_block_number()

            arbitrage_opportunities = []
            exchange_pairs = [(ex1, ex2) for i, ex1 in enumerate(exchanges) for ex2 in exchanges[i+1:]]
            
            for ex1, ex2 in exchange_pairs:
                for symbol in rates_by_exchange[ex1]:
                    if symbol in rates_by_exchange[ex2]:
                        rate1 = float(rates_by_exchange[ex1][symbol]['funding_rate'])
                        rate2 = float(rates_by_exchange[ex2][symbol]['funding_rate'])

                        if rate1 > rate2:
                            long_exchange, short_exchange = ex2, ex1
                            long_rate, short_rate = rate2, rate1
                        else:
                            long_exchange, short_exchange = ex1, ex2
                            long_rate, short_rate = rate1, rate2

                        arbitrage_opportunity = {
                            'long_exchange': long_exchange,
                            'short_exchange': short_exchange,
                            'symbol': symbol,
                            'long_exchange_funding_rate': long_rate,
                            'short_exchange_funding_rate': short_rate,
                            'block_number': block_number
                        }
                        arbitrage_opportunities.append(arbitrage_opportunity)

            return arbitrage_opportunities

        except Exception as e:
            logger.error(f'MatchingEngine - Error while finding arbitrage opportunities: {e}')
            return None


    def find_delta_neutral_arbitrage_opportunities(self, funding_rates):
        opportunities = []
        rates_by_symbol = group_by_symbol(funding_rates)
        for symbol, rates in rates_by_symbol.items():
            sorted_rates = sort_funding_rates_by_value(rates)
            opportunities.extend(self.find_arbitrage_opportunities_for_symbol(sorted_rates))
        return opportunities
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
            exchange_pairs = [(ex1, ex2) for i, ex1 in enumerate(list(exchanges)) for ex2 in list(exchanges)[i+1:]]
            print(f'exchange_pairs = {exchange_pairs}')

            for ex1, ex2 in exchange_pairs:
                common_symbols = set(rates_by_exchange[ex1].keys()) & set(rates_by_exchange[ex2].keys())
                for symbol in common_symbols:
                    rate1 = float(rates_by_exchange[ex1][symbol]['funding_rate'])
                    rate2 = float(rates_by_exchange[ex2][symbol]['funding_rate'])
                    skew1 = rates_by_exchange[ex1][symbol]['skew']
                    skew2 = rates_by_exchange[ex2][symbol]['skew']

                    if (rate1 > 0 and rate2 > 0) or (rate1 < 0 and rate2 < 0):
                        if rate1 > rate2:
                            long_exchange, short_exchange = ex2, ex1
                            long_rate, short_rate = rate2, rate1
                            long_exchange_skew, short_exchange_skew = skew2, skew1
                        else:
                            long_exchange, short_exchange = ex1, ex2
                            long_rate, short_rate = rate1, rate2
                            long_exchange_skew, short_exchange_skew = skew1, skew2
                    elif rate1 > 0 and rate2 < 0:
                        long_exchange, short_exchange = ex2, ex1
                        long_rate, short_rate = rate2, rate1
                        long_exchange_skew, short_exchange_skew = skew2, skew1
                    elif rate1 < 0 and rate2 > 0:
                        long_exchange, short_exchange = ex1, ex2
                        long_rate, short_rate = rate1, rate2
                        long_exchange_skew, short_exchange_skew = skew1, skew2

                    arbitrage_opportunity = {
                        'long_exchange': long_exchange,
                        'short_exchange': short_exchange,
                        'symbol': symbol,
                        'long_exchange_funding_rate': long_rate,
                        'short_exchange_funding_rate': short_rate,
                        'long_exchange_skew': long_exchange_skew,
                        'short_exchange_skew': short_exchange_skew,
                        'block_number': block_number
                    }
                    arbitrage_opportunities.append(arbitrage_opportunity)

            return arbitrage_opportunities

        except Exception as e:
            logger.error(f'MatchingEngine - Error while finding arbitrage opportunities: {e}')
            return None


    def find_delta_neutral_arbitrage_opportunities(self, funding_rates) -> list:
        opportunities = []
        if not funding_rates:
            logger.error("MatchingEngine - Funding rates are empty or not passed correctly.")
            return opportunities

        try:
            rates_by_symbol = group_by_symbol(funding_rates)
            for symbol, rates in rates_by_symbol.items():
                if not rates or not all('symbol' in rate for rate in rates):
                    logger.error(f'MatchingEngine - Missing "symbol" in one or more rate items for symbol group: {symbol}')
                    continue 

                sorted_rates = sort_funding_rates_by_value(rates)
                if sorted_rates:
                    opportunities.extend(self.find_arbitrage_opportunities_for_symbol(sorted_rates))

        except KeyError as ke:
            logger.error(f'MatchingEngine - KeyError - Missing key in data processing: {ke}')
        except TypeError as te:
            logger.error(f'MatchingEngine - TypeError - Issue with data types during processing: {te}')
        except Exception as e:
            logger.error(f'MatchingEngine - Unexpected error during processing: {e}')

        return opportunities


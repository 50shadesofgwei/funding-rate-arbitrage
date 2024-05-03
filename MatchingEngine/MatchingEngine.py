from MatchingEngine.MatchingEngineUtils import *
from GlobalUtils.logger import *

class matchingEngine:
    def __init__(self):
        pass
    
    def find_arbitrage_opportunities_for_symbol(self, sorted_rates):
        try:
            synthetix_rates = [rate for rate in sorted_rates if rate['exchange'] == 'Synthetix']
            binance_rates = [rate for rate in sorted_rates if rate['exchange'] == 'Binance']
            
            synthetix_dict = {normalize_symbol(rate['symbol']): rate for rate in synthetix_rates}
            binance_dict = {normalize_symbol(rate['symbol']): rate for rate in binance_rates}

            block_number = get_base_block_number()
            
            arbitrage_opportunities = []
            for symbol in synthetix_dict:
                if symbol in binance_dict:
                    snx_rate = float(synthetix_dict[symbol]['funding_rate'])
                    binance_rate = float(binance_dict[symbol]['funding_rate'])
                    skew = synthetix_dict[symbol]['skew']
                    funding_velocity = synthetix_dict[symbol]['funding_velocity']

                    if snx_rate > binance_rate:
                        long_exchange = 'Binance'
                        short_exchange = 'Synthetix'
                        long_rate = binance_rate
                        short_rate = snx_rate
                    else:
                        long_exchange = 'Synthetix'
                        short_exchange = 'Binance'
                        long_rate = snx_rate
                        short_rate = binance_rate

                    arbitrage_opportunity = {
                        'long_exchange': long_exchange,
                        'short_exchange': short_exchange,
                        'symbol': symbol,
                        'long_exchange_funding_rate': long_rate,
                        'short_exchange_funding_rate': short_rate,
                        'skew': skew,
                        'funding_velocity': funding_velocity,
                        'block_number': block_number
                    }
                    arbitrage_opportunities.append(arbitrage_opportunity)
            
            return arbitrage_opportunities
        
        except Exception as e:
            logger.error(f'MatchingEngine - Error while finding arbitrage opportunities for symbol {symbol}: {e}')
            return None

    def find_delta_neutral_arbitrage_opportunities(self, funding_rates):
        opportunities = []
        rates_by_symbol = group_by_symbol(funding_rates)
        for symbol, rates in rates_by_symbol.items():
            sorted_rates = sort_funding_rates_by_value(rates)
            opportunities.extend(self.find_arbitrage_opportunities_for_symbol(sorted_rates))
        return opportunities
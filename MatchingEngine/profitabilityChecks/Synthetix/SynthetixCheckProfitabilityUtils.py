from GlobalUtils.marketDirectory import MarketDirectory
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *


def estimate_time_to_neutralize_funding_rate_synthetix(opportunity: dict, size: float):
        try:
            symbol = str(opportunity['symbol'])
            if not symbol:
                logger.error(f"SynthetixCheckProfitabilityUtils - Missing 'symbol' in opportunity data: {opportunity}")
                return None

            is_long = opportunity['long_exchange'] == 'Synthetix'
            skew = float(opportunity['long_exchange_skew']) if is_long else float(opportunity['short_exchange_skew'])
            if skew is None:
                logger.error(f"SynthetixCheckProfitabilityUtils - Missing 'skew' in opportunity data: {opportunity}")
                return None

            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            size_after_fee = size * (1 - fee)
            adjusted_size = get_adjusted_size(size_after_fee, is_long)

            current_funding_rate: float = float(opportunity['long_exchange_funding_rate']) if is_long else float(opportunity['short_exchange_funding_rate'])
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol, skew, adjusted_size)
            funding_velocity_1hr = funding_velocity / 24

            if funding_velocity == 0 or current_funding_rate == 0:
                logger.error(f"SynthetixCheckProfitabilityUtils - No change in funding velocity or zero funding rate for {symbol}, cannot calculate neutralization time.")
                return 'No Neutralization'

            if current_funding_rate > 0 and current_funding_rate + (funding_velocity * 10) > 0:
                return 'No Neutralization'
            elif current_funding_rate < 0 and current_funding_rate + (funding_velocity * 10) < 0:
                return 'No Neutralization'

            hours_to_neutralize: float = abs(current_funding_rate / funding_velocity_1hr)
            return hours_to_neutralize
            

        except Exception as e:
            logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None
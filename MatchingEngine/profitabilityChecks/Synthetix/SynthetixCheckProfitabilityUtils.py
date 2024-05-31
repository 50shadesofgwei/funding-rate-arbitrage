from GlobalUtils.marketDirectory import MarketDirectory
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
from math import floor


def estimate_synthetix_profit(time_period_hours: float, size: float, opportunity: dict) -> float:
        is_long: bool = opportunity['long_exchange'] == 'Synthetix'
        symbol = str(opportunity['symbol'])
        skew: float = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']

        try:
            is_long = opportunity['long_exchange'] == 'Synthetix'
            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            fee_size = size * fee
            size_after_fee = size - fee_size
            
            # premium = self.position_controller.synthetix.calculate_premium(symbol, size_after_fee)
            # if premium is None:
            #     logger.error(f"CheckProfitability - Failed to calculate premium for {symbol}.")
            #     return None

            # size_with_premium = size_after_fee + premium
            adjusted_size = get_adjusted_size(size_after_fee, is_long)

            current_block_number = get_base_block_number()
            initial_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol=symbol, current_skew=skew, trade_size=adjusted_size)

            end_block_number = current_block_number + floor(BLOCKS_PER_HOUR_BASE * time_period_hours)
            total_funding = 0
            for block in range(current_block_number, end_block_number + 1):
                adjusted_rate = calculate_adjusted_funding_rate(initial_rate, funding_velocity, 1)
                profit_loss_per_day = adjusted_rate * adjusted_size
                if (is_long and adjusted_rate < 0) or (not is_long and adjusted_rate > 0):
                    profit_loss_per_day *= -1

                total_funding += profit_loss_per_day / BLOCKS_PER_DAY_BASE

            return total_funding

        except Exception as e:
            logger.error(f'SynthetixCheckProfitabilityUtils -  Error estimating Synthetix profit for {symbol}: Error: {e}')
            return None

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

            if funding_velocity * current_funding_rate < 0:
                logger.info(f"SynthetixCheckProfitabilityUtils - Funding rate and velocity have the same sign for {symbol}; rate will not neutralize.")
                return 'No Neutralization'

            hours_to_neutralize: float = current_funding_rate / funding_velocity_1hr
            logger.info(f"SynthetixCheckProfitabilityUtils - Hours to neutralize calculated at {hours_to_neutralize}.")
            return hours_to_neutralize
            

        except Exception as e:
            logger.error(f'CSynthetixCheckProfitabilityUtils - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None
from GlobalUtils.MarketDirectories.SynthetixMarketDirectory import SynthetixMarketDirectory
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from math import floor


def estimate_time_to_neutralize_funding_rate_synthetix(opportunity: dict, size_usd: float):
        try:
            symbol = str(opportunity['symbol'])
            if not symbol:
                logger.error(f"SynthetixCheckProfitabilityUtils - Missing 'symbol' in opportunity data: {opportunity}")
                return None

            is_long = opportunity['long_exchange'] == 'Synthetix'
            skew_in_asset = float(opportunity['long_exchange_skew']) if is_long else float(opportunity['short_exchange_skew'])
            if skew_in_asset is None:
                logger.error(f"SynthetixCheckProfitabilityUtils - Missing 'skew' in opportunity data: {opportunity}")
                return None

            size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, size_usd)
            adjusted_size_in_asset = get_adjusted_size(size_in_asset, is_long)

            current_funding_rate: float = float(opportunity['long_exchange_funding_rate']) if is_long else float(opportunity['short_exchange_funding_rate'])
            funding_velocity = SynthetixMarketDirectory.calculate_new_funding_velocity(symbol, skew_in_asset, adjusted_size_in_asset)
            funding_velocity_1hr = funding_velocity / 24

            if funding_velocity == 0 or current_funding_rate == 0:
                logger.error(f"SynthetixCheckProfitabilityUtils - No change in funding velocity or zero funding rate for {symbol}, cannot calculate neutralization time.")
                return 'No Neutralization'

            if current_funding_rate > 0 and funding_velocity > 0:
                return 'No Neutralization'
            elif current_funding_rate < 0 and funding_velocity < 0:
                return 'No Neutralization'

            hours_to_neutralize: float = abs(current_funding_rate / funding_velocity_1hr)
            return hours_to_neutralize
            

        except Exception as e:
            logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None

def calculate_expected_funding_for_time_period_usd(opportunity: dict, is_long: bool, size_usd: float, time_period_hours: float):
    symbol = opportunity['symbol']
    try:
        skew_usd = opportunity['skew_usd']
        price = get_price_from_pyth(symbol)
        skew_in_asset = skew_usd / price
        adjusted_size_usd = get_adjusted_size(size_usd, is_long)
        adjusted_size_in_asset = adjusted_size_usd / price
        initial_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
        funding_velocity_24h = SynthetixMarketDirectory.calculate_new_funding_velocity(symbol=symbol, current_skew=skew_in_asset, trade_size=adjusted_size_in_asset)

        total_funding = calculate_profit(
            size_usd,
            time_period_hours,
            funding_velocity_24h,
            initial_rate
        )
        
        return total_funding
    
    except Exception as e:
            logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating usd profit for symbol {symbol}: {e}')
            return None

def calculate_profit(size_usd: float, time_period_hours: float, funding_velocity_24h: float, initial_funding_rate: float) -> float:
    try:
        funding_change_per_hour = funding_velocity_24h / 24
        final_funding_rate = initial_funding_rate + (funding_change_per_hour * time_period_hours)
        average_funding_rate = (initial_funding_rate + final_funding_rate) / 2
        profit = average_funding_rate * size_usd * time_period_hours
        
        return profit
    
    except Exception as e:
        logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating profit via average rate for period, size_usd = {size_usd}, time_period_hours = {time_period_hours}, funding_velocity_24h = {funding_velocity_24h}, initial_funding_rate = {initial_funding_rate}: {e}')
        return None

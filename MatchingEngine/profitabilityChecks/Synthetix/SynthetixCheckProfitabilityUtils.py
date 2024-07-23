from GlobalUtils.MarketDirectories.SynthetixMarketDirectory import SynthetixMarketDirectory
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from APICaller.Synthetix.SynthetixCaller import GLOBAL_SYNTHETIX_CLIENT # TODO - delete this


def estimate_time_to_neutralize_funding_rate_synthetix(opportunity: dict, absolute_size_usd: float):
        try:
            symbol = str(opportunity['symbol'])
            is_long = opportunity['long_exchange'] == 'Synthetix'
            skew_usd = float(opportunity['long_exchange_skew_usd']) if is_long else float(opportunity['short_exchange_skew_usd'])
            skew_in_asset = get_asset_amount_for_given_dollar_amount(symbol, skew_usd)

            size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, absolute_size_usd)
            adjusted_size_in_asset = get_adjusted_size(size_in_asset, is_long)


            current_funding_rate: float = float(opportunity['long_exchange_funding_rate_8hr']) if is_long else float(opportunity['short_exchange_funding_rate_8hr'])
            current_funding_rate_24h = current_funding_rate * 3
            funding_velocity = SynthetixMarketDirectory.calculate_new_funding_velocity(
                symbol, 
                skew_in_asset, 
                adjusted_size_in_asset
            )

            if funding_velocity == 0 or current_funding_rate == 0:
                logger.error(f"SynthetixCheckProfitabilityUtils - No change in funding velocity or zero funding rate for {symbol}, cannot calculate neutralization time.")
                return 'No Neutralization'

            if current_funding_rate > 0 and funding_velocity > 0:
                return 'No Neutralization'
            elif current_funding_rate < 0 and funding_velocity < 0:
                return 'No Neutralization'

            velocity_per_hour = funding_velocity / 24
            hours_to_neutralize: float = abs(current_funding_rate_24h / velocity_per_hour)

            return hours_to_neutralize
            

        except Exception as e:
            logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None


def calculate_expected_funding_for_time_period_usd(opportunity: dict, is_long: bool, absolute_size_usd: float, time_period_hours: float):
    symbol = opportunity['symbol']
    try:
        skew_usd = opportunity['long_exchange_skew_usd'] if is_long else opportunity['short_exchange_skew_usd']
        skew_in_asset = get_asset_amount_for_given_dollar_amount(symbol, skew_usd)
        adjusted_size_usd = get_adjusted_size(absolute_size_usd, is_long)
        adjusted_size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, adjusted_size_usd)
        initial_rate_8h = opportunity['long_exchange_funding_rate_8hr'] if is_long else opportunity['short_exchange_funding_rate_8hr']
        initial_rate_24h = initial_rate_8h * 3
        funding_velocity_24h = SynthetixMarketDirectory.calculate_new_funding_velocity(
            symbol, 
            skew_in_asset, 
            adjusted_size_in_asset)

        total_funding = calculate_profit(
            absolute_size_usd,
            time_period_hours,
            funding_velocity_24h,
            initial_rate_24h
        )

        return total_funding
    
    except Exception as e:
            logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating usd profit for symbol {symbol}: {e}')
            return None

def calculate_profit(absolute_size_usd: float, time_period_hours: float, funding_velocity_24h: float, initial_funding_rate_24h: float) -> float:
    try:
        funding_change_per_hour = (funding_velocity_24h / 24)
        final_funding_rate = initial_funding_rate_24h + (funding_change_per_hour * time_period_hours)
        average_daily_funding_rate = (initial_funding_rate_24h + final_funding_rate) / 2
        profit_per_day = abs(average_daily_funding_rate) * absolute_size_usd
        days = time_period_hours / 24
        profit = abs(profit_per_day * days)

        return profit
    
    except Exception as e:
        logger.error(f'SynthetixCheckProfitabilityUtils - Error estimating profit via average rate for period, size_usd = {absolute_size_usd}, time_period_hours = {time_period_hours}, funding_velocity_24h = {funding_velocity_24h}, initial_funding_rate = {initial_funding_rate_24h}: {e}')
        return None

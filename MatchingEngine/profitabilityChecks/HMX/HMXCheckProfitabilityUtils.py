from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from APICaller.HMX.HMXCallerUtils import calculate_daily_funding_velocity
from math import floor


def estimate_HMX_profit(time_period_hours: float, size_usd: float, opportunity: dict):
    try:
        is_long = opportunity['long_exchange'] == 'HMX'
        symbol = opportunity['symbol']
        skew = opportunity['long_exchange_skew_usd'] if is_long else opportunity['short_exchange_skew_usd']
        adjusted_skew = skew + size_usd if is_long else skew - size_usd
        funding_rate = opportunity['long_exchange_funding_rate_8hr'] if is_long else opportunity['short_exchange_funding_rate_8hr']
        funding_rate = funding_rate / 100

        daily_velocity = calculate_daily_funding_velocity(symbol=symbol, skew_usd=adjusted_skew)
        daily_velocity = daily_velocity / 100
        funding_rate_change_per_minute = daily_velocity / (24 * 60)
        funding_rate_per_minute = funding_rate / (8 * 60)
        total_profit = 0
        time_period_mins = time_period_hours * 60

        for min in range(int(floor(time_period_mins))):
            profit_per_min = funding_rate_per_minute * size_usd

            if is_long:
                profit_per_min = -profit_per_min if funding_rate_change_per_minute > 0 else profit_per_min
            else:
                profit_per_min = profit_per_min if funding_rate_change_per_minute > 0 else -profit_per_min

            funding_rate_per_minute += funding_rate_change_per_minute
            total_profit += profit_per_min

        return total_profit

    except Exception as e:
        logger.error(f'CheckProfitability - Error estimating HMX profit for {symbol}: {e}')
        return None


def estimate_time_to_neutralize_funding_rate_hmx(opportunity: dict, size_usd: float) -> float | str:
        try:
            symbol = str(opportunity['symbol'])
            is_long = opportunity['long_exchange'] == 'HMX'
            skew = float(opportunity['long_exchange_skew_usd']) if is_long else float(opportunity['short_exchange_skew_usd'])
            adjusted_skew = skew + size_usd if is_long else skew - size_usd
            daily_velocity = calculate_daily_funding_velocity(symbol=symbol, skew_usd=adjusted_skew)
            daily_velocity = daily_velocity / 100
            hourly_velocity: float = daily_velocity / 24 

            current_funding_rate = float(opportunity['long_exchange_funding_rate_8hr']) if is_long else float(opportunity['short_exchange_funding_rate_8hr'])
    
            if current_funding_rate == 0:
                logger.error(f"HMXCheckProfitabilityUtils - Zero funding rate for {symbol}, cannot calculate neutralization time.")
                return None
            
            if current_funding_rate > 0 and current_funding_rate + (daily_velocity * 10) > 0:
                return 'No Neutralization'
            elif current_funding_rate < 0 and current_funding_rate + (daily_velocity * 10) < 0:
                return 'No Neutralization'
            else:
                hours_to_neutralize: float = abs(current_funding_rate / hourly_velocity)
                return hours_to_neutralize
        except Exception as e:
            logger.error(f'HMXCheckProfitabilityUtils - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None

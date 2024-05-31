from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from APICaller.HMX.HMXCallerUtils import calculate_daily_funding_velocity
from math import floor


def estimate_HMX_profit(time_period_hours: float, size: float, opportunity: dict):
        try:
            is_long = opportunity['long_exchange'] == 'HMX'
            symbol = opportunity['symbol']
            skew = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']
            dollar_size = get_dollar_amount_for_given_asset_amount(symbol, size)
            total_profit: float = 0

            daily_velocity = calculate_daily_funding_velocity(skew)
            hourly_velocity = daily_velocity / 24 
            hourly_funding_rate = hourly_velocity / 100  

            for hour in range(int(floor(time_period_hours))):
                hourly_profit = hourly_funding_rate * dollar_size

                if is_long:
                    total_profit += hourly_profit 
                else:
                    total_profit -= hourly_profit

            return total_profit

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating HMX profit for {symbol}: {e}')
            return None

def estimate_time_to_neutralize_funding_rate_hmx(opportunity: dict, size: float) -> float | str:
        try:
            symbol = str(opportunity['symbol'])
            is_long = opportunity['long_exchange'] == 'HMX'
            
            skew = float(opportunity['long_exchange_skew']) if is_long else float(opportunity['short_exchange_skew'])
            
            daily_velocity = calculate_daily_funding_velocity(skew)
            print(type(daily_velocity))
            hourly_velocity: float = daily_velocity / 24 

            current_funding_rate = float(opportunity['long_exchange_funding_rate']) if is_long else float(opportunity['short_exchange_funding_rate'])
    

            if current_funding_rate == 0:
                logger.error(f"CheckProfitability - Zero funding rate for {symbol}, cannot calculate neutralization time.")
                return None
            
            if hourly_velocity == 0:
                logger.info(f"CheckProfitability - Zero funding velocity for {symbol}, neutralization cannot be calculated.")
                return "No Neutralization"

            if hourly_velocity * current_funding_rate < 0:
                logger.info(f"CheckProfitability - Funding rate and velocity have the same sign for {symbol}; rate will not neutralize.")
                return "No Neutralization"
            else:
                hours_to_neutralize: float = current_funding_rate / hourly_velocity
                return hours_to_neutralize
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None

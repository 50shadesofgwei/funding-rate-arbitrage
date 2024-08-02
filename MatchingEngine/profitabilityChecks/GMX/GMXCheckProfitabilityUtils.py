from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from APICaller.GMX.GMXCallerUtils import ARBITRUM_CONFIG_OBJECT
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

def calculate_profit_gmx(absolute_size_usd: float, time_period_hours: float, funding_velocity_24h: float, initial_funding_rate_24h: float) -> float:
    try:
        funding_change_per_hour = (funding_velocity_24h / 24)
        final_funding_rate = initial_funding_rate_24h + (funding_change_per_hour * time_period_hours)
        average_daily_funding_rate = (initial_funding_rate_24h + final_funding_rate) / 2
        profit_per_day = abs(average_daily_funding_rate) * absolute_size_usd
        days = time_period_hours / 24
        profit = abs(profit_per_day * days)

        return profit
    
    except Exception as e:
        logger.error(f'GMXCheckProfitabilityUtils - Error estimating profit via average rate for period, size_usd = {absolute_size_usd}, time_period_hours = {time_period_hours}, funding_velocity_24h = {funding_velocity_24h}, initial_funding_rate = {initial_funding_rate_24h}: {e}')
        return None

def estimate_time_to_neutralize_funding_rate_gmx(opportunity: dict, absolute_size_usd: float, open_interest: dict) -> float | str:
        try:
            symbol = str(opportunity['symbol'])
            is_long = opportunity['long_exchange'] == 'GMX'
            daily_velocity = GMXMarketDirectory.calculate_new_funding_velocity(
                symbol=symbol, 
                absolute_trade_size_usd=absolute_size_usd,
                is_long=is_long,
                open_interest=open_interest
                )
            hourly_velocity: float = daily_velocity / 24 

            current_funding_rate = float(opportunity['long_exchange_funding_rate_8hr']) if is_long else float(opportunity['short_exchange_funding_rate_8hr'])
            hourly_funding_rate_apr = ((current_funding_rate * 3) * 365) / 24
    
            if current_funding_rate == 0:
                logger.error(f"GMXCheckProfitabilityUtils - Zero funding rate for {symbol}, cannot calculate neutralization time.")
                return None
            
            if current_funding_rate > 0 and current_funding_rate + (daily_velocity * 10) > 0:
                return 'No Neutralization'
            elif current_funding_rate < 0 and current_funding_rate + (daily_velocity * 10) < 0:
                return 'No Neutralization'
            else:
                hours_to_neutralize: float = abs(hourly_funding_rate_apr / hourly_velocity)
                return hours_to_neutralize
        except Exception as e:
            logger.error(f'GMXCheckProfitabilityUtils - Error estimating time to neutralize funding rate for {symbol}: {e}', exc_info=True)
            return None
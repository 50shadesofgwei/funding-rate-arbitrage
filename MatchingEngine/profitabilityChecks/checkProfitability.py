from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from TxExecution.HMX.HMXPositionControllerUtils import get_market_for_symbol
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from GlobalUtils.marketDirectory import MarketDirectory
from APICaller.HMX.HMXCallerUtils import *
import math
import json
from math import floor
import os

class ProfitabilityChecker:
    def __init__(self):
        self.position_controller = MasterPositionController()
        self.default_trade_duration = float(os.getenv('DEFAULT_TRADE_DURATION_HOURS'))
        self.default_trade_size_usd = float(os.getenv('DEFAULT_TRADE_SIZE_USD')) * float(self.position_controller.synthetix.leverage_factor)


    def find_most_profitable_opportunity(self, opportunities):
        logger.info(f'CheckProfitability - Debugging: Initial Opportunities = {opportunities}')
        enhanced_opportunities = []
        trade_size_usd = self.default_trade_size_usd

        for opportunity in opportunities:
            logger.info(f'CheckProfitability - Evaluating opportunity: {opportunity}')
            symbol = opportunity['symbol']
            size = get_asset_amount_for_given_dollar_amount(symbol, trade_size_usd)
            size_per_exchange = size / 2

            profit_details = {}
            for role in ['long', 'short']:
                exchange = opportunity[f'{role}_exchange']
                time_to_neutralize = self.estimate_time_to_neutralize_funding_rate_for_exchange(
                    opportunity, size_per_exchange, exchange)
                if time_to_neutralize is None:
                    profit_details[f'{role}_exchange_profit_loss'] = self.default_trade_size_usd * float(opportunity[f'{role}_exchange_funding_rate'])
                    logger.info(f'CheckProfitability - No neutralization expected for {role} on {exchange}')
                else:
                    profit = self.estimate_profit_for_exchange(time_to_neutralize, size_per_exchange, opportunity, exchange)
                    profit_details[f'{role}_exchange_profit_loss'] = profit or 0

            total_profit_usd = sum(profit_details.values())
            profit_details['total_profit_usd'] = total_profit_usd

            opportunity.update({
                'profit_details': profit_details,
                'total_profit_usd': total_profit_usd
            })
            enhanced_opportunities.append(opportunity)

        # Sorting opportunities based on estimated profit in USD
        enhanced_opportunities.sort(key=lambda x: x['total_profit_usd'], reverse=True)

        if enhanced_opportunities:
            filename = 'OrderedOpportunities.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(enhanced_opportunities, f, ensure_ascii=False, indent=4)
        else:
            logger.info("CheckProfitability - No profitable opportunities found.")

        return enhanced_opportunities

    def estimate_profit_for_exchange(self, time_period_hours: float, size: float, opportunity: dict, exchange: str) -> float:
        try:
            if exchange == 'Binance':
                estimated_profit = self.estimate_binance_profit(time_period_hours, size, opportunity)
                return estimated_profit
            elif exchange == 'Synthetix':
                estimated_profit = self.estimate_synthetix_profit(time_period_hours, size, opportunity)
                return estimated_profit
            elif exchange == 'HMX':
                estimated_profit = self.estimate_HMX_profit(time_period_hours, size, opportunity)
                return estimated_profit
        
        except Exception as e:
            logger.error(f'CheckProfitability - Failed to estimate profit for exchange {exchange}, Error: {e}')


    def estimate_synthetix_profit(self, time_period_hours, size, opportunity):
        is_long = opportunity['long_exchange'] == 'Synthetix'
        symbol = opportunity.get('symbol')
        skew = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']

        try:
            is_long = opportunity['long_exchange'] == 'Synthetix'
            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            fee_size = size * fee
            size_after_fee = size - fee_size
            
            premium = self.position_controller.synthetix.calculate_premium(symbol, size_after_fee)
            if premium is None:
                logger.error(f"CheckProfitability - Failed to calculate premium for {symbol}.")
                return None
            
            size_with_premium = size_after_fee * (1 + premium)
            adjusted_size = get_adjusted_size(size_with_premium, is_long)

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
            logger.error(f'CheckProfitability - Error estimating Synthetix profit for {symbol}: {str(e)}')
            return None


    def estimate_HMX_profit(self, time_period_hours: float, size: float, opportunity):
        try:
            is_long = opportunity['long_exchange'] == 'HMX'
            symbol = opportunity['symbol']
            skew = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']
            dollar_size = get_dollar_amount_for_given_asset_amount(symbol, size)
            total_profit: float = 0

            daily_velocity = calculate_daily_funding_velocity(skew)
            hourly_velocity = daily_velocity / 24 
            hourly_funding_rate = hourly_velocity / 100  

            for hour in range(int(math.floor(time_period_hours))):
                hourly_profit = hourly_funding_rate * dollar_size

                if is_long:
                    total_profit += hourly_profit 
                else:
                    total_profit -= hourly_profit

            return total_profit

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating HMX profit for {symbol}: {e}')
            return None

    def estimate_time_to_neutralize_funding_rate_for_exchange(self, opportunity: dict, size: float, exchange: str):
        if exchange == "HMX":
            time_to_neutralize = self.estimate_time_to_neutralize_funding_rate_hmx(opportunity, size)
            return time_to_neutralize
        elif exchange == "Synthetix":
            time_to_neutralize = self.estimate_time_to_neutralize_funding_rate_synthetix(opportunity, size)
            return time_to_neutralize
        else:
            return None

    def estimate_time_to_neutralize_funding_rate_hmx(self, opportunity: dict, size: float):
        try:
            symbol = opportunity['symbol']
            is_long = opportunity['long_exchange'] == 'HMX'
            
            skew = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']
            
            daily_velocity = calculate_daily_funding_velocity(skew)
            hourly_velocity = daily_velocity / 24 

            current_funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            if current_funding_rate == 0:
                logger.error(f"CheckProfitability - Zero funding rate for {symbol}, cannot calculate neutralization time.")
                return self.default_trade_duration
            
            if hourly_velocity == 0:
                logger.info(f"CheckProfitability - Zero funding velocity for {symbol}, neutralization cannot be calculated.")
                return self.default_trade_duration

            if hourly_velocity * current_funding_rate < 0:
                return None
            else:
                logger.info(f"CheckProfitability - Funding rate and velocity have the same sign for {symbol}; rate will not neutralize.")
                return None
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None


    def estimate_time_to_neutralize_funding_rate_synthetix(self, opportunity: dict, size: float):
        try:
            symbol = opportunity.get('symbol')
            if not symbol:
                logger.error(f"CheckProfitability - Missing 'symbol' in opportunity data: {opportunity}")
                return None

            is_long = opportunity['long_exchange'] == 'Synthetix'
            skew = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']
            if skew is None:
                logger.error(f"CheckProfitability - Missing 'skew' in opportunity data: {opportunity}")
                return None

            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            size_after_fee = size * (1 - fee)
            adjusted_size = get_adjusted_size(size_after_fee, is_long)

            current_funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol, skew, adjusted_size)

            if funding_velocity == 0 or current_funding_rate == 0:
                logger.error(f"CheckProfitability - No change in funding velocity or zero funding rate for {symbol}, cannot calculate neutralization time.")
                return None

            if funding_velocity * current_funding_rate < 0:
                return None

            logger.info(f"CheckProfitability - Funding rate and velocity have the same sign for {symbol}; rate will not neutralize.")
            return None

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None

    def estimate_binance_profit(self, time_period_hours: float, size: float, opportunity: dict):
        try:
            symbol = opportunity['symbol']
            is_long = opportunity['long_exchange'] == 'Binance'
            funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            current_block_number = get_base_block_number()
            size = get_adjusted_size(size, is_long)

            binance_funding_events = get_binance_funding_event_schedule(current_block_number)
            end_block_number = current_block_number + BLOCKS_PER_HOUR_BASE * time_period_hours

            total_profit_loss = 0
            for event_block in binance_funding_events:
                if current_block_number <= event_block <= end_block_number:
                    profit_loss_per_event = funding_rate * size
                    if (is_long and funding_rate > 0) or (not is_long and funding_rate < 0):
                        profit_loss_per_event *= -1
                    
                    total_profit_loss += profit_loss_per_event

            return total_profit_loss
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating Binance profit for {symbol}: {e}')
            return None

    def estimate_profit_for_time_period(self, hours_to_neutralize_by_exchange, size: float, opportunity):
        try:
            symbol = opportunity.get('symbol')
            long_exchange: str = opportunity['long_exchange']
            short_exchange: str = opportunity['short_exchange']
            hours_to_neutralize_long = float(hours_to_neutralize_by_exchange['long_exchange'])
            hours_to_neutralize_short = float(hours_to_neutralize_by_exchange['short_exchange'])

            long_exchange_profit_loss = self.estimate_profit_for_exchange(hours_to_neutralize_long, size, opportunity, long_exchange)
            short_exchange_profit_loss = self.estimate_profit_for_exchange(hours_to_neutralize_short, size, opportunity, short_exchange)
            logger.error(f'Debug - CheckProfitabiility: {long_exchange} pnl: {long_exchange_profit_loss}, {short_exchange} pnl: {short_exchange_profit_loss}')
            total_profit_loss = long_exchange_profit_loss + short_exchange_profit_loss

            pnl_dict = {
                'symbol': symbol,
                'total_profit_loss': total_profit_loss,
                'long_exchange_profit_loss': long_exchange_profit_loss,
                'short_exchange_profit_loss': short_exchange_profit_loss
            }
            logger.info(f'CheckProfitability - PnL calculated successfully for {symbol}. pnl_dict={pnl_dict}')
            return pnl_dict

        except ValueError as ve:
            logger.error(f'CheckProfitability - Validation Error: {ve}')
            return None
        except Exception as e:
            logger.error(f'CheckProfitability - Unexpected error when estimating profit for {symbol} for time period: {e}')
            return None





from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from GlobalUtils.marketDirectory import MarketDirectory
from APICaller.HMX.HMXCallerUtils import *
from MatchingEngine.profitabilityChecks.HMX.HMXCheckProfitabilityUtils import *
from MatchingEngine.profitabilityChecks.Synthetix.SynthetixCheckProfitabilityUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
import json
import os

class ProfitabilityChecker:
    def __init__(self):
        self.position_controller = MasterPositionController()
        self.default_trade_duration = float(os.getenv('DEFAULT_TRADE_DURATION_HOURS'))
        self.default_trade_size_usd = float(os.getenv('DEFAULT_TRADE_SIZE_USD')) * float(self.position_controller.synthetix.leverage_factor)


    def find_most_profitable_opportunity(self, opportunities: list, is_demo: bool):
        trade_size_usd = self.default_trade_size_usd
        best_opportunity = None
        max_profit = 0
        opportunities_with_profit = []

        for opportunity in opportunities:
            symbol = opportunity['symbol']
            size = get_asset_amount_for_given_dollar_amount(symbol, trade_size_usd)
            size_per_exchange = size / 2
            total_profit_usd = 0

            for role in ['long', 'short']:
                exchange = opportunity[f'{role}_exchange']
                time_to_neutralize = self.estimate_time_to_neutralize_funding_rate_for_exchange(
                    opportunity, size_per_exchange, exchange)

                if time_to_neutralize == "No Neutralization":
                    profit_loss = self.default_trade_size_usd * float(opportunity[f'{role}_exchange_funding_rate'])
                else:
                    profit_loss = self.estimate_profit_for_exchange(
                        time_to_neutralize, size_per_exchange, opportunity, exchange)
                    profit_loss = profit_loss if profit_loss is not None else 0

                opportunity[f'{role}_exchange_profit_loss'] = profit_loss
                total_profit_usd += profit_loss

            opportunity['total_profit_usd'] = total_profit_usd
            opportunities_with_profit.append(opportunity)

            if total_profit_usd > max_profit:
                max_profit = total_profit_usd
                best_opportunity = opportunity

        opportunities_with_profit.sort(key=lambda x: x['total_profit_usd'], reverse=True)

        if is_demo:
            return opportunities_with_profit
        else:
            with open('OrderedOpportunities.json', 'w') as file:
                json.dump(opportunities_with_profit, file, indent=4)
            return best_opportunity

    def estimate_profit_for_exchange(self, time_period_hours: float, size: float, opportunity: dict, exchange: str) -> float:
        try:
            if exchange == 'Binance':
                estimated_profit = self.estimate_binance_profit(time_period_hours=time_period_hours, size=size, opportunity=opportunity)
                return estimated_profit
            elif exchange == 'Synthetix':
                estimated_profit = self.estimate_synthetix_profit(time_period_hours=time_period_hours, size=size, opportunity=opportunity)
                return estimated_profit
            elif exchange == 'HMX':
                estimated_profit = estimate_HMX_profit(time_period_hours=time_period_hours, size=size, opportunity=opportunity)
                return estimated_profit
        
        except Exception as e:
            logger.error(f'CheckProfitability - Failed to estimate profit for exchange {exchange}, Error: {e}')


    def estimate_time_to_neutralize_funding_rate_for_exchange(self, opportunity: dict, size: float, exchange: str):
        if exchange == "HMX":
            time_to_neutralize = estimate_time_to_neutralize_funding_rate_hmx(opportunity, size)
            return time_to_neutralize
        elif exchange == "Synthetix":
            time_to_neutralize = estimate_time_to_neutralize_funding_rate_synthetix(opportunity, size)
            return time_to_neutralize
        else:
            return None

    def estimate_synthetix_profit(self, time_period_hours: float, size: float, opportunity: dict) -> float:
        is_long: bool = opportunity['long_exchange'] == 'Synthetix'
        symbol = str(opportunity['symbol'])
        skew: float = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']

        try:
            is_long = opportunity['long_exchange'] == 'Synthetix'
            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            fee_size = size * fee
            size_after_fee = size - fee_size
            
            premium = self.position_controller.synthetix.calculate_premium(symbol, size_after_fee)
            if premium is None:
                logger.error(f"CheckProfitability - Failed to calculate premium for {symbol}.")
                return None

            size_with_premium = size_after_fee + premium
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
            logger.error(f'SynthetixCheckProfitabilityUtils -  Error estimating Synthetix profit for {symbol}: Error: {e}')
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
            symbol = opportunity['symbol']
            long_exchange = opportunity['long_exchange']
            short_exchange = opportunity['short_exchange']
            hours_to_neutralize_long = hours_to_neutralize_by_exchange['long_exchange']
            hours_to_neutralize_short = hours_to_neutralize_by_exchange['short_exchange']

            long_profit_loss = 0
            if hours_to_neutralize_long == "No Neutralization":
                long_profit_loss = self.default_trade_size_usd * float(opportunity['long_exchange_funding_rate'])
            else:
                long_profit_loss = self.estimate_profit_for_exchange(hours_to_neutralize_long, size, opportunity, long_exchange)

            short_profit_loss = 0
            if hours_to_neutralize_short == "No Neutralization":
                short_profit_loss = self.default_trade_size_usd * float(opportunity['short_exchange_funding_rate'])
            else:
                short_profit_loss = self.estimate_profit_for_exchange(hours_to_neutralize_short, size, opportunity, short_exchange)

            total_profit_loss = long_profit_loss + short_profit_loss

            pnl_dict = {
                'symbol': symbol,
                'total_profit_loss': total_profit_loss,
                'long_exchange_profit_loss': long_profit_loss,
                'short_exchange_profit_loss': short_profit_loss
            }

            return pnl_dict

        except ValueError as ve:
            logger.error(f'CheckProfitability - Validation Error: {ve}')
            return None
        except Exception as e:
            logger.error(f'CheckProfitability - Unexpected error when estimating profit for {symbol}: {e}')
            return None






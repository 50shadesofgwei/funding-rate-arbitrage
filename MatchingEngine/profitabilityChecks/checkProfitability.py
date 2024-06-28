from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
from GlobalUtils.marketDirectory import MarketDirectory
from APICaller.HMX.HMXCallerUtils import *
from MatchingEngine.profitabilityChecks.HMX.HMXCheckProfitabilityUtils import *
from MatchingEngine.profitabilityChecks.Synthetix.SynthetixCheckProfitabilityUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
from APICaller.ByBit.ByBitCaller import ByBitCaller
import json
import os

class ProfitabilityChecker:
    def __init__(self):
        self.position_controller = MasterPositionController()
        self.bybit_caller = ByBitCaller()
        self.default_trade_duration = float(os.getenv('DEFAULT_TRADE_DURATION_HOURS'))
        self.default_trade_size_usd = float(os.getenv('DEFAULT_TRADE_SIZE_USD')) * float(self.position_controller.synthetix.leverage_factor)


    def find_most_profitable_opportunity(self, opportunities: list, is_demo: bool):
        try:
            trade_size_usd = self.default_trade_size_usd
            best_opportunity = None
            max_profit = 0
            opportunities_with_profit = []

            for opportunity in opportunities:
                size_per_exchange = trade_size_usd / 2
                total_profit_usd = 0
                hours_to_neutralize_by_exchange = {}

                for role in ['long', 'short']:
                    exchange = opportunity[f'{role}_exchange']
                    time_to_neutralize = self.estimate_time_to_neutralize_funding_rate_for_exchange(
                        opportunity, 
                        size_per_exchange, 
                        exchange
                    )

                    if time_to_neutralize == None:
                        logger.error(f'CheckProfitability - NoneType returned while estimating time to neutralize rate.')
                        return None

                    if time_to_neutralize == "No Neutralization":
                        hours_to_neutralize_by_exchange[f'{role}_exchange'] = self.default_trade_duration
                    else:
                        time_period_hours = time_to_neutralize
                        hours_to_neutralize_by_exchange[f'{role}_exchange'] = time_period_hours
                        opportunity['trade_duration_estimate'] = time_to_neutralize

                pnl_dict = self.estimate_profit_for_time_period(hours_to_neutralize_by_exchange, trade_size_usd, opportunity)
                opportunity['total_profit_usd'] = float(pnl_dict['total_profit_loss'])
                opportunity['long_exchange_profit_usd'] = float(pnl_dict['long_exchange_profit_loss'])
                opportunity['short_exchange_profit_usd'] = float(pnl_dict['short_exchange_profit_loss'])
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
        
        except Exception as e:
            logger.error(f'CheckProfitability - Failed to find most profitable opportunity. Error: {e}')

    def estimate_profit_for_exchange(self, time_period_hours: float, size_usd: float, opportunity: dict, exchange: str) -> float:
        try:
            if exchange == 'Binance':
                estimated_profit = self.estimate_binance_profit(time_period_hours=time_period_hours, size_usd=size_usd, opportunity=opportunity)
                return estimated_profit
            elif exchange == 'Synthetix':
                estimated_profit = self.estimate_synthetix_profit(time_period_hours=time_period_hours, size_usd=size_usd, opportunity=opportunity)
                return estimated_profit
            elif exchange == 'HMX':
                estimated_profit = estimate_HMX_profit(time_period_hours=time_period_hours, size_usd=size_usd, opportunity=opportunity)
                return estimated_profit
            elif exchange == 'ByBit':
                estimated_profit = self.estimate_bybit_profit(time_period_hours=time_period_hours, size_usd=size_usd, opportunity=opportunity)
                return estimated_profit
        
        except Exception as e:
            logger.error(f'CheckProfitability - Failed to estimate profit for exchange {exchange}, Error: {e}')
            return None

    def estimate_time_to_neutralize_funding_rate_for_exchange(self, opportunity: dict, size_usd: float, exchange: str):
        try:
            if exchange == "HMX":
                time_to_neutralize = estimate_time_to_neutralize_funding_rate_hmx(opportunity, size_usd)
                if type(time_to_neutralize) == str:
                    time_to_neutralize = self.default_trade_duration
                    return time_to_neutralize
                else:
                    return time_to_neutralize

            if exchange == "Synthetix":
                time_to_neutralize = estimate_time_to_neutralize_funding_rate_synthetix(opportunity, size_usd)
                if type(time_to_neutralize) == str:
                    time_to_neutralize = self.default_trade_duration
                    return time_to_neutralize
                else:
                    return time_to_neutralize

            elif exchange == "ByBit":
                return "No Neutralization"

            elif exchange == "Binance":
                return "No Neutralization"

        except Exception as e:
            logger.error(f'CheckProfitability - Failed to estimate profit for exchange {exchange}, Error: {e}')
            return None

    def estimate_synthetix_profit(self, time_period_hours: float, size_usd: float, opportunity: dict) -> float:
        is_long: bool = opportunity['long_exchange'] == 'Synthetix'
        symbol = str(opportunity['symbol'])
        skew: float = opportunity['long_exchange_skew'] if is_long else opportunity['short_exchange_skew']

        try:
            is_long = opportunity['long_exchange'] == 'Synthetix'
            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            fee_size = size_usd * fee
            size_after_fee = size_usd - fee_size
            
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

    def estimate_binance_profit(self, time_period_hours: float, size_usd: float, opportunity: dict):
        try:
            symbol = opportunity['symbol']
            is_long = opportunity['long_exchange'] == 'Binance'
            funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            current_block_number = get_base_block_number()
            size_usd = get_adjusted_size(size_usd, is_long)

            binance_funding_events = get_binance_funding_event_schedule(current_block_number)
            end_block_number = current_block_number + BLOCKS_PER_HOUR_BASE * time_period_hours

            total_profit_loss = 0
            for event_block in binance_funding_events:
                if current_block_number <= event_block <= end_block_number:
                    profit_loss_per_event = funding_rate * size_usd
                    if (is_long and funding_rate > 0) or (not is_long and funding_rate < 0):
                        profit_loss_per_event *= -1
                    
                    total_profit_loss += profit_loss_per_event

            return total_profit_loss

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating Binance profit for {symbol}: {e}')
            return None

    def estimate_bybit_profit(self, time_period_hours: float, size_usd: float, opportunity: dict) -> float:
        try:
            symbol = opportunity['symbol'] + 'USDT'
            is_long = opportunity['long_exchange'] == 'ByBit'
            funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            number_of_funding_events_in_time_period = self.bybit_caller.get_next_funding_events_for_time_period(symbol, time_period_hours)

            if is_long:
                if funding_rate > 0:
                    # rate positive, long
                    profit_loss_usd_per_event = size_usd * funding_rate
                    profit_loss_usd_per_event = -profit_loss_usd_per_event
                else:
                    # rate negative, long
                    profit_loss_usd_per_event = size_usd * abs(funding_rate)
            else:
                if funding_rate > 0:
                    # rate positive, short
                    profit_loss_usd_per_event = size_usd * funding_rate
                else:
                    # rate negative, short
                    profit_loss_usd_per_event = size_usd * abs(funding_rate)
                    profit_loss_usd_per_event = -profit_loss_usd_per_event

            profit_loss_usd_for_time_period = profit_loss_usd_per_event * number_of_funding_events_in_time_period

            return profit_loss_usd_for_time_period

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating ByBit profit for {symbol}: {e}')
            return None

    def estimate_profit_for_time_period(self, hours_to_neutralize_by_exchange: dict, size_usd: float, opportunity: dict) -> dict:
        try:
            symbol = opportunity['symbol']
            long_exchange = opportunity['long_exchange']
            short_exchange = opportunity['short_exchange']
            hours_to_neutralize_long = hours_to_neutralize_by_exchange['long_exchange']
            hours_to_neutralize_short = hours_to_neutralize_by_exchange['short_exchange']
            long_exchange_funding_rate = float(opportunity['long_exchange_funding_rate'])
            long_exchange_funding_rate_1hr = long_exchange_funding_rate / 8
            short_exchange_funding_rate = float(opportunity['short_exchange_funding_rate'])
            short_exchange_funding_rate_1hr = short_exchange_funding_rate / 8
            shortest_time = float(min(hours_to_neutralize_long, hours_to_neutralize_short))


            long_profit_loss = 0
            if hours_to_neutralize_long == "No Neutralization":
                long_profit_loss = self.default_trade_size_usd * long_exchange_funding_rate_1hr * shortest_time
            else:
                long_profit_loss = self.estimate_profit_for_exchange(shortest_time, size_usd, opportunity, long_exchange)

            short_profit_loss = 0
            if hours_to_neutralize_short == "No Neutralization":
                short_profit_loss = self.default_trade_size_usd * short_exchange_funding_rate_1hr * shortest_time
            else:
                short_profit_loss = self.estimate_profit_for_exchange(shortest_time, size_usd, opportunity, short_exchange)

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






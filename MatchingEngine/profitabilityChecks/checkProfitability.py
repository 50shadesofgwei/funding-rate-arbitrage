from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
from MatchingEngine.profitabilityChecks.checkProfitabilityUtils import *
import json
from math import floor
import os

class ProfitabilityChecker:
    def __init__(self):
        self.position_controller = MasterPositionController()
        self.default_trade_duration = float(os.getenv('DEFAULT_TRADE_DURATION_HOURS'))
        self.default_trade_size_usd = float(os.getenv('DEFAULT_TRADE_SIZE_USD')) * float(os.getenv('TRADE_LEVERAGE'))
    
    def find_most_profitable_opportunity(self, opportunities):
        enhanced_opportunities = []
        trade_size_usd = self.default_trade_size_usd

        for opportunity in opportunities:
            symbol = opportunity['symbol']
            full_symbol = get_full_asset_name(symbol)
            size = get_asset_amount_for_given_dollar_amount(full_symbol, trade_size_usd)
            size_per_exchange = size / 2
            hours_to_neutralize = self.estimate_time_to_neutralize_funding_rate(opportunity, size_per_exchange)
            profit_estimate_dict = self.estimate_profit_for_time_period(hours_to_neutralize, size_per_exchange, opportunity)
            profit_estimate_in_asset = profit_estimate_dict['total_profit_loss']
            profit_estimate_usd = get_dollar_amount_for_given_asset_amount(full_symbol, profit_estimate_in_asset)

            opportunity['profit_estimate_usd'] = profit_estimate_usd
            opportunity['profit_details'] = profit_estimate_dict
            opportunity['hours_to_neutralize'] = hours_to_neutralize
            enhanced_opportunities.append(opportunity)

        enhanced_opportunities.sort(key=lambda x: x['profit_estimate_usd'], reverse=True)

        if enhanced_opportunities:
            filename = 'OrderedOpportunities.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(enhanced_opportunities, f, ensure_ascii=False, indent=4)
        else:
            logger.info("CheckProfitability - No profitable opportunities found.")

        return enhanced_opportunities[0]

    def estimate_synthetix_profit(self, time_period_hours, size, opportunity):
        try:
            symbol = opportunity['symbol']
            skew = opportunity['skew']
            is_long = opportunity['long_exchange'] == 'Synthetix'
            
            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            fee_size = size * fee
            size_after_fee = size - fee_size
            slippage = self.position_controller.synthetix.calculate_slippage(symbol, size_after_fee)
            if slippage is not None: 
                size_with_slippage = size_after_fee * (1 + slippage)
            else:
                size_with_slippage = size_after_fee

            adjusted_size = get_adjusted_size(size_with_slippage, is_long)

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
            logger.error(f'CheckProfitability - Error estimating Synthetix profit for {symbol}: {e}')
            return None


    def estimate_time_to_neutralize_funding_rate(self, opportunity, size):
        try:
            symbol = opportunity['symbol']
            skew = opportunity['skew']
            is_long = opportunity['long_exchange'] == 'Synthetix'
            fee = MarketDirectory.get_maker_taker_fee(symbol, skew, is_long)
            size_after_fee = size * (1 - fee)
            size = get_adjusted_size(size_after_fee, is_long)

            current_funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol, skew, size)

            if funding_velocity == 0 or current_funding_rate == 0:
                logger.error(f"CheckProfitability - No change in funding velocity or zero funding rate for {symbol}, cannot calculate neutralization time.")
                return self.default_trade_duration

            if funding_velocity * current_funding_rate < 0:
                funding_velocity_per_block = funding_velocity / BLOCKS_PER_DAY_BASE
                blocks_to_neutral = -current_funding_rate / funding_velocity_per_block
                if funding_velocity == 0:
                    logger.info(f"CheckProfitability - Zero funding velocity for {symbol}, neutralization cannot be calculated.")
                    return self.default_trade_duration

                if current_funding_rate * funding_velocity >= 0:
                    logger.info(f"CheckProfitability - Funding rate and velocity have the same sign for {symbol}; rate will not neutralize.")
                    return self.default_trade_duration

                hours_to_neutral = blocks_to_neutral / BLOCKS_PER_HOUR_BASE

                return hours_to_neutral
            else:
                return self.default_trade_duration

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return None

    def estimate_binance_profit(self, time_period_hours, size, opportunity):
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

    def estimate_profit_for_time_period(self, time_period_hours, size, opportunity):
        try:
            symbol = opportunity['symbol']
            snx_profit_loss = self.estimate_synthetix_profit(time_period_hours, size, opportunity)
            binance_profit_loss = self.estimate_binance_profit(time_period_hours, size, opportunity)
            total_profit_loss = snx_profit_loss + binance_profit_loss

            pnl_dict = {
                'symbol': symbol,
                'total_profit_loss': total_profit_loss,
                'snx_profit_loss': snx_profit_loss,
                'binance_profit_loss': binance_profit_loss
            }

            logger.info(f'DEBUGGING: PnL dict = {pnl_dict}')

            return pnl_dict
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating profit for {symbol} over {time_period_hours} hours: {e}')
            return None


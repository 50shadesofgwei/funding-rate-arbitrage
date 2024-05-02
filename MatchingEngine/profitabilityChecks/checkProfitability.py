from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
import json

class ProfitabilityChecker:
    def __init__(self):
        self.position_controller = MasterPositionController()
    
    def find_most_profitable_opportunity(self, opportunities, time_period_hours=1):
        enhanced_opportunities = []
        trade_size_usd = 10_000

        for opportunity in opportunities:
            symbol = opportunity['symbol']
            full_symbol = get_full_asset_name(symbol)
            size = get_asset_amount_for_given_dollar_amount(full_symbol, trade_size_usd)
            profit_estimate_dict = self.estimate_profit_for_time_period(time_period_hours, size, opportunity)
            profit_estimate_in_asset = profit_estimate_dict['total_profit_loss']
            profit_estimate = get_dollar_amount_for_given_asset_amount(full_symbol, profit_estimate_in_asset)
            neutralization_estimate = self.estimate_time_to_neutralize_funding_rate(opportunity, size)

            opportunity['profit_estimate_usd'] = profit_estimate
            opportunity['profit_details'] = profit_estimate_dict
            opportunity['neutralization_estimate'] = neutralization_estimate
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

            current_block_number = get_base_block_number()
            initial_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            original_funding_velocity = opportunity['funding_velocity']
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol=symbol, current_skew=skew, trade_size=size_after_fee)
            
            logger.info(f'DEBUGGING - Symbol = {symbol}. Skew = {skew}. Trade size = {size}. Funding rate = {initial_rate}. Original velocity = {original_funding_velocity}. New velocity = {funding_velocity}')

            blocks_per_hour = 1800
            end_block_number = current_block_number + blocks_per_hour * time_period_hours
            total_funding = 0

            for block in range(current_block_number, end_block_number + 1):
                adjusted_rate = calculate_adjusted_funding_rate(initial_rate, funding_velocity, 1)
                total_funding += (adjusted_rate * size_after_fee) / BLOCKS_PER_DAY_BASE

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

            current_funding_rate = opportunity['long_exchange_funding_rate'] if is_long else opportunity['short_exchange_funding_rate']
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol, skew, size_after_fee)

            logger.info(f"Current funding rate for symbol {symbol}: {current_funding_rate:.8f}, Funding velocity: {funding_velocity:.8f}")

            if funding_velocity == 0 or current_funding_rate == 0:
                logger.error(f"No change in funding velocity or zero funding rate for {symbol}, cannot calculate neutralization time.")
                return {'hours_until_neutralization': 'infinite', 'neutralization_profit_usd': None}

            if funding_velocity * current_funding_rate < 0:
                blocks_per_hour = 1800
                blocks_to_neutral = abs(current_funding_rate / (funding_velocity / BLOCKS_PER_DAY_BASE))
                hours_to_neutral = blocks_to_neutral / blocks_per_hour
                logger.info(f"Blocks to neutralization: {blocks_to_neutral}, Hours: {hours_to_neutral}")

                total_profit = 0
                current_rate = current_funding_rate
                for block in range(int(blocks_to_neutral)):
                    adjusted_rate = calculate_adjusted_funding_rate(current_rate, funding_velocity, 1) 
                    total_profit += (abs(adjusted_rate) * size_after_fee) / BLOCKS_PER_DAY_BASE
                    current_rate = adjusted_rate

                logger.info(f'Total profit for symbol {symbol} calculated at {total_profit} at end of loop')

                full_asset_name = get_full_asset_name(symbol)
                total_profit_usd = get_dollar_amount_for_given_asset_amount(full_asset_name, total_profit)
                return {'hours_until_neutralization': "{:.2f}".format(hours_to_neutral), 'neutralization_profit_usd': "{:.6f}".format(total_profit_usd)}
            else:
                return {'hours_until_neutralization': 'infinite', 'neutralization_profit_usd': None}

        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating time to neutralize funding rate for {symbol}: {e}')
            return {'hours_until_neutralization': None, 'neutralization_profit_usd': None}


    def estimate_binance_profit(self, time_period_hours, size, opportunity):
        try:
            symbol = opportunity['symbol']
            funding_rate = opportunity['long_exchange_funding_rate'] if opportunity['long_exchange'] == 'Binance' else opportunity['short_exchange_funding_rate']
            current_block_number = get_base_block_number()

            binance_funding_events = get_binance_funding_event_schedule(current_block_number)
            blocks_per_hour = 1800
            end_block_number = current_block_number + blocks_per_hour * time_period_hours

            total_profit_loss = 0
            for event_block in binance_funding_events:
                if current_block_number <= event_block <= end_block_number:
                    total_profit_loss += funding_rate * size

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

            return pnl_dict
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating profit for {symbol} over {time_period_hours} hours: {e}')
            return None


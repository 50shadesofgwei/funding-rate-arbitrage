from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate
import json

class ProfitabilityChecker:
    def __init__(self):
        self.position_controller = MasterPositionController()
    
    def find_most_profitable_opportunity(self, opportunities, time_period_hours=8):
        enhanced_opportunities = []
        trade_size_usd = self.position_controller.get_trade_size(opportunities[0])

        for opportunity in opportunities:
            symbol = opportunity['symbol']
            full_symbol = get_full_asset_name(symbol)
            size = get_asset_amount_for_given_dollar_amount(full_symbol, trade_size_usd)
            profit_estimate_dict = self.estimate_profit_for_time_period(time_period_hours, size, opportunity)
            profit_estimate_in_asset = profit_estimate_dict['total_profit_loss']
            profit_estimate = get_dollar_amount_for_given_asset_amount(full_symbol, profit_estimate_in_asset)

            opportunity['profit_estimate_usd'] = profit_estimate
            opportunity['profit_details'] = profit_estimate_dict
            enhanced_opportunities.append(opportunity)

        enhanced_opportunities.sort(key=lambda x: x['profit_estimate_usd'], reverse=True)

        if enhanced_opportunities:
            logger.info(f"CheckProfitability - Opportunities by profitability: {enhanced_opportunities}")
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
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol=symbol, current_skew=skew, trade_size=size_after_fee)
            
            blocks_per_hour = 1800
            end_block_number = current_block_number + blocks_per_hour * time_period_hours
            total_funding = 0

            for block in range(current_block_number, end_block_number + 1):
                blocks_since_start = block - current_block_number
                adjusted_rate = calculate_adjusted_funding_rate(initial_rate, funding_velocity, blocks_since_start)
                total_funding += (adjusted_rate * size_after_fee) / BLOCKS_PER_DAY_BASE

            return total_funding
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating Synthetix profit for {symbol}: {e}')
            return None

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


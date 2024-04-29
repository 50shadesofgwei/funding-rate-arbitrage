from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController
from Backtesting.Synthetix.SynthetixBacktesterUtils import calculate_adjusted_funding_rate

class ProfitabilityChecker:
    exchange_fees = {
        "Binance": 0.0004,  # 0.04% fee
        "Synthetix": 0    # gas fees handled elsewhere
    }

    def __init__(self):
        self.position_controller = MasterPositionController()

    def get_capital_amount(self, opportunity) -> float:
        capital = self.position_controller.get_trade_size(opportunity)
        return capital

    def get_exchange_fee(self, exchange: str) -> float:
        return self.exchange_fees.get(exchange, 0)

    def calculate_position_cost(self, fee_rate: float, opportunity) -> float:
        capital = self.get_capital_amount(opportunity)
        return capital * fee_rate
    
    def find_most_profitable_opportunity(self, opportunities, time_period_hours=8):
        max_profit = float('-inf')
        most_profitable = None

        for opportunity in opportunities:
            symbol = opportunity['asset']
            size = get_asset_amount_for_given_dollar_amount(symbol, 10000)
            profit_estimate_dict = self.estimate_profit_for_time_period(time_period_hours, size, opportunity)
            profit_estimate_in_asset = profit_estimate_dict['total_profit_loss']
            profit_estimate = get_dollar_amount_for_given_asset_amount(symbol, profit_estimate_in_asset)

            if profit_estimate > max_profit:
                max_profit = profit_estimate
                most_profitable = opportunity

        if most_profitable:
            position = "short" if most_profitable['short_exchange'] == 'Synthetix' else "long"
            logger.info(f"CheckProfitability - Best opportunity found with a profit of {max_profit}, suggested position: {position}, details: {most_profitable}")
        else:
            logger.info("CheckProfitability - No profitable opportunities found.")

        return most_profitable


    def estimate_synthetix_profit(self, time_period_hours, size, opportunity):
        try:
            symbol = opportunity['symbol']
            skew = opportunity['skew']

            current_block_number = get_base_block_number()
            initial_rate = opportunity['short_exchange_funding_rate'] if opportunity['short_exchange'] == 'Synthetix' else opportunity['long_exchange_funding_rate']
            funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol, skew, size)

            blocks_per_hour = 1800
            end_block_number = current_block_number + blocks_per_hour * time_period_hours
            total_funding = 0

            for block in range(current_block_number, end_block_number + 1):
                blocks_since_start = block - current_block_number
                adjusted_rate = calculate_adjusted_funding_rate(initial_rate, funding_velocity, blocks_since_start)
                total_funding += (adjusted_rate * size) / BLOCKS_PER_DAY_BASE

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

            snx_profit_loss = self.estimate_synthetix_profit()
            binance_profit_loss = self.estimate_binance_profit()
            total_profit_loss = snx_profit_loss + binance_profit_loss

            return {
                'total_profit_loss': total_profit_loss,
                'snx_profit_loss': snx_profit_loss,
                'binance_profit_loss': binance_profit_loss
            }
        except Exception as e:
            logger.error(f'CheckProfitability - Error estimating profit for {symbol} over {time_period_hours} hours: {e}')
            return None


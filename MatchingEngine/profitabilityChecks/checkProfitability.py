import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from TxExecution.Master.MasterPositionController import MasterPositionController

class ProfitabilityChecker:
    exchange_fees = {
        "Binance": 0.0004,  # 0.04% fee
        "Synthetix": 0    # gas fees handled elsewhere
    }

    def __init__(self):
        self.position_controller = MasterPositionController()

    @log_function_call
    def get_capital_amount(self, opportunity) -> float:
        capital = self.position_controller.get_trade_size(opportunity)
        return capital

    @log_function_call
    def get_exchange_fee(self, exchange: str) -> float:
        return self.exchange_fees.get(exchange, 0)

    @log_function_call
    def calculate_position_cost(self, fee_rate: float, opportunity) -> float:
        capital = self.get_capital_amount(opportunity)
        return capital * fee_rate
    
    @log_function_call
    def find_most_profitable_opportunity(self, opportunities):
        max_funding_rate = float('-inf')
        most_profitable = None
        for opportunity in opportunities:
            if opportunity["long_exchange"] == "Synthetix":
                funding_rate = float(opportunity["long_funding_rate"])
            elif opportunity["short_exchange"] == "Synthetix":
                funding_rate = float(opportunity["short_funding_rate"])
            else:
                continue

            # Use the absolute value of the funding rate for comparison
            abs_funding_rate = abs(funding_rate)
            if abs_funding_rate > max_funding_rate:
                max_funding_rate = abs_funding_rate
                most_profitable = opportunity

        if most_profitable:
            logger.info(f"Best opportunity found, details: {most_profitable}")
        else:
            logger.info("No profitable opportunities found.")

        return most_profitable
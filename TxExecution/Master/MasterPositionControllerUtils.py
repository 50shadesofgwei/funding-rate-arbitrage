import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

import sys
import os
from dotenv import load_dotenv
from GlobalUtils.logger import logger

load_dotenv()

def check_other_exchange_has_adequate_collateral(collateral_amounts, exchange: str, desired_collateral_amount: float) -> bool:
    collateral = collateral_amounts.get(exchange, 0)
    return collateral >= desired_collateral_amount

def adjust_collateral_allocation(
        collateral_amounts, 
        long_exchange, 
        short_exchange, 
        initial_percentage=75, 
        decrement=10, 
        attempts=3) -> float:

    max_collateral = get_max_collateral_from_selected_exchanges(collateral_amounts, long_exchange, short_exchange)
    desired_collateral = max_collateral * (initial_percentage / 100)

    for _ in range(attempts):
        if check_other_exchange_has_adequate_collateral(collateral_amounts, short_exchange, desired_collateral):
            return desired_collateral
        else:
            desired_collateral *= (1 - decrement / 100)

    raise ValueError(f"Not enough capital on {short_exchange} for the trade.")

def apply_leverage_to_trade_amount(trade_amount: float) -> float:
    leverage_factor = float(os.getenv('LEVERAGE_FACTOR'))
    trade_amount_with_leverage_factor = trade_amount * leverage_factor
    return trade_amount_with_leverage_factor

def get_max_collateral_from_selected_exchanges(collateral_amounts, primary_exchange, secondary_exchange):
    max_collateral_amount = max(collateral_amounts.get(primary_exchange, 0), collateral_amounts.get(secondary_exchange, 0))
    logger.info(f'max collateral amount found: {max_collateral_amount}')
    return max_collateral_amount



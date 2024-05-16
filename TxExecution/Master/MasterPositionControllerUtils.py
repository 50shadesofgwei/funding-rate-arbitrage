import os
from dotenv import load_dotenv
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *

load_dotenv()

def adjust_collateral_allocation(
        collateral_amounts, 
        long_exchange, 
        short_exchange) -> float:
    
    if not is_collateral_ratio_acceptable(collateral_amounts, long_exchange, short_exchange):
        raise ValueError("Collateral on exchanges does not meet the minimum ratio requirement - collateral amounts need rebalancing across exchanges")
    
    initial_percentage = int(os.getenv('PERCENTAGE_CAPITAL_PER_TRADE'))
    long_collateral = collateral_amounts.get(long_exchange, 0)
    short_collateral = collateral_amounts.get(short_exchange, 0)
    smaller_collateral = min(long_collateral, short_collateral)
    
    trade_amount = smaller_collateral * (initial_percentage / 100)
    return float(trade_amount)

def is_collateral_ratio_acceptable(collateral_amounts, long_exchange, short_exchange, min_ratio=0.01):
    long_collateral = collateral_amounts.get(long_exchange, 0)
    short_collateral = collateral_amounts.get(short_exchange, 0)
    
    if long_collateral >= short_collateral:
        ratio = short_collateral / long_collateral if long_collateral > 0 else 0
    else:
        ratio = long_collateral / short_collateral if short_collateral > 0 else 0
    
    logger.info(f'MasterPositionControllerUtils - collateral ratio between {long_exchange} and {short_exchange} = {ratio}')
    return ratio >= min_ratio

def calculate_adjusted_trade_size(opportunity, is_long: bool, trade_size: float) -> float:
        try:
            leverage_factor = os.getenv('TRADE_LEVERAGE')
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(opportunity['symbol'], trade_size)
            trade_size_with_leverage = trade_size_in_asset * leverage_factor
            adjusted_trade_size = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            logger.info(f'MasterPositionControlerUtils - levered trade size in asset calculated at {adjusted_trade_size}')
            return adjusted_trade_size
        except Exception as e:
            logger.error(f"MasterPositionControlerUtils - Failed to calculate adjusted trade size. Error: {e}")
            raise



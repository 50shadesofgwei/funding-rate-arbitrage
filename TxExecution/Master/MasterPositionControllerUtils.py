import os
from dotenv import load_dotenv
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *

load_dotenv()

def adjust_collateral_allocation(collateral_amounts: dict, long_exchange: str, short_exchange: str) -> float:
    try:
        if not is_collateral_ratio_acceptable(collateral_amounts, long_exchange, short_exchange):
            logger.error(f"Collateral on exchanges does not meet the minimum ratio requirement - collateral amounts need rebalancing between {long_exchange} and {short_exchange}")
            return None

        initial_percentage = int(os.getenv('PERCENTAGE_CAPITAL_PER_TRADE'))
        long_collateral = collateral_amounts['long_exchange']
        short_collateral = collateral_amounts['short_exchange']
        smaller_collateral = min(long_collateral, short_collateral)
        
        trade_amount = float(smaller_collateral * (initial_percentage / 100))
        logger.info(f'TRADE AMOUNT = {trade_amount}')
        return trade_amount

    except Exception as e:
        logger.info(f'MasterPositionControllerUtils - Failed to determine trade size in function adjust_collateral_allocation. Error: {e}')
        return None

def is_collateral_ratio_acceptable(collateral_amounts, long_exchange, short_exchange, min_ratio=0.01):
    try:
        long_collateral = collateral_amounts['long_exchange']
        short_collateral = collateral_amounts['long_exchange']
        
        if long_collateral >= short_collateral:
            ratio = short_collateral / long_collateral if long_collateral > 0 else 0
        else:
            ratio = long_collateral / short_collateral if short_collateral > 0 else 0
        
        logger.info(f'MasterPositionControllerUtils - collateral ratio between {long_exchange} and {short_exchange} = {ratio}')
        return ratio >= min_ratio
    
    except Exception as e:
        logger.info(f'MasterPositionControllerUtils - Failed to calculate whether collateral ratio across exchanges met the minimum requirement. Ratio: {ratio}, Minimum: {min_ratio} Error: {e}')
        return False

def calculate_adjusted_trade_size(opportunity, is_long: bool, trade_size: float) -> float:
        try:
            leverage_factor = float(os.getenv('TRADE_LEVERAGE'))
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(opportunity['symbol'], trade_size)
            trade_size_with_leverage = trade_size_in_asset * leverage_factor
            adjusted_trade_size = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            logger.info(f'MasterPositionControlerUtils - levered trade size in asset calculated at {adjusted_trade_size}')
            return adjusted_trade_size
        except Exception as e:
            logger.error(f"MasterPositionControlerUtils - Failed to calculate adjusted trade size. Error: {e}")
            return None



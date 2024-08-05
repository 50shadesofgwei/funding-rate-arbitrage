import os
from dotenv import load_dotenv
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *

load_dotenv()

def adjust_collateral_allocation(collateral_amounts: dict, long_exchange: str, short_exchange: str) -> float:
    try:
        initial_percentage = float(os.getenv('PERCENTAGE_CAPITAL_PER_TRADE'))

        if not is_collateral_ratio_acceptable(collateral_amounts):
            logger.error(f"MasterPositionControllerUtils - Collateral on exchanges does not meet the minimum ratio requirement - collateral amounts need rebalancing between {long_exchange} and {short_exchange}")
            return None

        long_collateral = float(collateral_amounts['long_exchange'])
        short_collateral = float(collateral_amounts['short_exchange'])
        smaller_collateral = min(long_collateral, short_collateral)

        initial_collateral_percentage = initial_percentage / 100
        trade_amount = smaller_collateral * initial_collateral_percentage

        return trade_amount

    except Exception as e:
        logger.error(f'MasterPositionControllerUtils - Failed to determine trade size in adjust_collateral_allocation. Error: {e}')
        return None


def is_collateral_ratio_acceptable(collateral_amounts: dict, min_ratio=0.01):
    try:
        long_collateral = collateral_amounts['long_exchange']
        short_collateral = collateral_amounts['long_exchange']
        
        if long_collateral >= short_collateral:
            ratio = short_collateral / long_collateral if long_collateral > 0 else 0
        else:
            ratio = long_collateral / short_collateral if short_collateral > 0 else 0
        
        return ratio >= min_ratio
    
    except Exception as e:
        logger.error(f'MasterPositionControllerUtils - Failed to calculate whether collateral ratio across exchanges met the minimum requirement. Ratio: {ratio}, Minimum: {min_ratio} Error: {e}')
        return False

def calculate_adjusted_trade_size(opportunity: dict, is_long: bool, trade_size: float) -> float:
        try:
            leverage_factor = float(os.getenv('TRADE_LEVERAGE'))
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(opportunity['symbol'], trade_size)
            trade_size_with_leverage = trade_size_in_asset * leverage_factor
            adjusted_trade_size = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            
            return adjusted_trade_size
        except Exception as e:
            logger.error(f"MasterPositionControlerUtils - Failed to calculate adjusted trade size. Error: {e}")
            return None


def get_is_hedge(opportunity: dict):
    try:
        long_rate = abs(opportunity['long_exchange_funding_rate_8hr'])
        short_rate = abs(opportunity['short_exchange_funding_rate_8hr'])

        if long_rate > short_rate:
            is_hedge = {
                'long': False,
                'short': True
            }
            return is_hedge
        
        else:
            is_hedge = {
                'long': True,
                'short': False
            }
            return is_hedge

    except Exception as e:
        logger.error(f"MasterPositionControlerUtils - Failed to calculate which side is the hedge. Error: {e}")
        return None


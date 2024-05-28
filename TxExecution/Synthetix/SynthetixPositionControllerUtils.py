from PositionMonitor.Synthetix.SynthetixPositionMonitor import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from decimal import DivisionByZero
import re
import uuid

ALL_MARKET_IDS = [
    100,
    200
]

def parse_trade_data_from_position_details(position_details) -> dict:
    try:
        side = get_side(position_details['position']['position_size'])
        symbol = position_details['position']['symbol']
        asset_price = get_price_from_pyth(symbol)
        liquidation_price = calculate_liquidation_price(position_details, asset_price)
        order_id_hash = uuid.uuid4()
        order_id = order_id_hash.int % (10**18)

        trade_data = {
            "exchange": "Synthetix",
            "symbol": position_details['position']['symbol'],
            "side": side,
            "size": position_details['position']['position_size'],
            "order_id": order_id,
            "liquidation_price": liquidation_price
        }
        return trade_data

    except KeyError as e:
        logger.error(f"SynthetixPositionControllerUtils - KeyError in parse_trade_data_from_position_details: {e}")
        return {}
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - An unexpected error occurred in parse_trade_data_from_position_details: {e}")
        return {}

@log_function_call
def calculate_liquidation_price(position_data, asset_price: float) -> float:
    try:
        position_size = Decimal(str(position_data['position']['position_size']))
        available_margin = Decimal(str(position_data['margin_details']['available_margin']))
        maintenance_margin_requirement = Decimal(str(position_data['margin_details']['maintenance_margin_requirement']))
        initial_margin_requirement = Decimal(str(position_data['margin_details']['initial_margin_requirement']))
        current_asset_price = Decimal(asset_price)

        if initial_margin_requirement <= 0 or position_size == 0 or current_asset_price <= 0:
            raise ValueError("Invalid input values for calculating liquidation price.")

        is_long = position_size > 0

        if is_long:
            liquidation_price = (available_margin - maintenance_margin_requirement + (position_size * current_asset_price)) / position_size
        else:
            liquidation_price = (available_margin - maintenance_margin_requirement - (position_size * current_asset_price)) / position_size

        return float(liquidation_price)
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - Error in calculating liquidation price: {e}")
        return None

def get_side(size: float) -> str:
    try:
        if size > 0:
            return 'Long'
        elif size < 0:
            return 'Short'
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - Error determining side from size {size}: {e}")
        return 'Error'
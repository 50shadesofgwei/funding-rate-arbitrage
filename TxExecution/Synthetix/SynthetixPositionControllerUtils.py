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

@log_function_call
def parse_trade_data_from_position_details(position_details) -> dict:
    try:
        side = get_side(position_details['position']['position_size'])
        full_asset_name = get_full_asset_name(position_details['position']['symbol'])
        asset_price = get_asset_price(full_asset_name)
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
def is_transaction_hash(tx_hash) -> bool:
    # Regular expression to match an Ethereum transaction hash
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return re.match(pattern, tx_hash) is not None

@log_function_call
def calculate_liquidation_price(position_data, asset_price: float) -> float:
    try:
        position_size = Decimal(str(position_data['position']['position_size']))
        available_margin = Decimal(str(position_data['margin_details']['available_margin']))
        maintenance_margin_requirement = Decimal(str(position_data['margin_details']['maintenance_margin_requirement']))
        initial_margin_requirement = Decimal(str(position_data['margin_details']['initial_margin_requirement']))
        current_asset_price = Decimal(asset_price)

        # Basic checks
        if initial_margin_requirement <= 0 or position_size == 0 or current_asset_price <= 0:
            raise ValueError("Invalid input values for calculating liquidation price.")

        maintenance_margin_ratio = maintenance_margin_requirement / initial_margin_requirement
        is_long = position_size > 0
        abs_position_size = abs(position_size)
        price_difference = (available_margin / (abs_position_size * maintenance_margin_ratio)) - current_asset_price

        liquidation_price = current_asset_price - price_difference if is_long else current_asset_price + price_difference

        return float(liquidation_price)
    except (KeyError, ValueError, DivisionByZero, InvalidOperation) as e:
        logger.error(f"SynthetixPositionControllerUtils - Error in calculating liquidation price: {e}")
        return float('nan')

@log_function_call
def get_side(size: float) -> str:
    try:
        if size > 0:
            return 'Long'
        elif size < 0:
            return 'Short'
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - Error determining side from size {size}: {e}")
        return 'Error'
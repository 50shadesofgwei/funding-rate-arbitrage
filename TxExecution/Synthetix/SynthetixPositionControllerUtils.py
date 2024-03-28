import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from PositionMonitor.Synthetix.SynthetixPositionMonitor import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from decimal import DecimalException
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
        position = position_data['position']
        margin_details = position_data['margin_details']
        current_asset_price = Decimal(asset_price)

        position_size = Decimal(str(position['position_size']))
        available_margin = Decimal(str(margin_details['available_margin']))
        maintenance_margin_requirement = Decimal(str(margin_details['maintenance_margin_requirement']))
        initial_margin_requirement = Decimal(str(margin_details['initial_margin_requirement']))

        # Ensure position_size, maintenance_margin_requirement, and current_asset_price are not zero to avoid DivisionByZero error
        if initial_margin_requirement <= 0:
            logger.error("SynthetixPositionControllerUtils - Initial margin requirement is zero or negative, cannot calculate liquidation price.")
            return float('nan')

        # Check position size
        if position_size == 0:
            logger.error("SynthetixPositionControllerUtils - Position size is zero, cannot calculate liquidation price.")
            return float('nan')

        # Check current asset price
        if current_asset_price == 0:
            logger.error("SynthetixPositionControllerUtils - Current asset price is zero, cannot calculate liquidation price.")
            return float('nan')

        maintenance_margin_ratio = maintenance_margin_requirement / initial_margin_requirement if initial_margin_requirement > 0 else Decimal('0.5')

        # Calculate bankruptcy price, ensuring divisor is not zero
        divisor = (position_size * maintenance_margin_ratio * current_asset_price)
        if divisor == 0:
            logger.error("SynthetixPositionControllerUtils - Division by zero encountered in bankruptcy price calculation.")
            return float('nan')

        bankruptcy_price = available_margin / divisor
        liquidation_price = current_asset_price + (bankruptcy_price - current_asset_price) / Decimal('1.05')

        return float(liquidation_price)
    except KeyError as e:
        logger.error(f"SynthetixPositionControllerUtils - Key error in calculating liquidation price: {e}")
    except DecimalException as e:
        logger.error(f"SynthetixPositionControllerUtils - Decimal operation error in calculating liquidation price: {e}")
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - Unexpected error in calculating liquidation price: {e}")

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
from PositionMonitor.Synthetix.SynthetixPositionMonitor import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from decimal import DivisionByZero
import re
import uuid


def parse_trade_data_from_position_details(position_details: dict) -> dict:
    try:
        logger.error(f'SynthetixPositionControllerUtils:parse_trade_data_from_position_details - position_details = {position_details}')
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

        logger.info(f'SynthetixPositionControllerUtils - trade_data = {trade_data}')
        return trade_data

    except KeyError as e:
        logger.error(f"SynthetixPositionControllerUtils - KeyError in parse_trade_data_from_position_details: {e}")
        return {}
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - An unexpected error occurred in parse_trade_data_from_position_details: {e}")
        return {}

@log_function_call
def calculate_liquidation_price(position_data: dict, asset_price: float) -> float:
    try:
        logger.error(f'SynthetixPositionControllerUtils:calculate_liquidation_price - position_data = {position_data}')
        position_size = position_data['position']['position_size']
        available_margin = position_data['margin_details']['available_margin']
        maintenance_margin_requirement = position_data['margin_details']['maintenance_margin_requirement']

        logger.debug(f"SynthetixPositionControllerUtils - Calculating liquidation price with position_size={position_size}, available_margin={available_margin}, maintenance_margin_requirement={maintenance_margin_requirement}, asset_price={asset_price}")

        if not position_size:
            logger.error(f"SynthetixPositionControllerUtils - Invalid position size: {position_size}. Cannot calculate liquidation price.")
            return None
        if asset_price <= 0:
            logger.error(f"SynthetixPositionControllerUtils - Invalid asset price: {asset_price}. Cannot calculate liquidation price.")
            return None
        if available_margin <= 0 or maintenance_margin_requirement < 0:
            logger.error(f"SynthetixPositionControllerUtils - Invalid margin values: Available={available_margin}, Maintenance Requirement={maintenance_margin_requirement}.")
            return None

        is_long = position_size > 0
        if is_long:
            liquidation_price = (available_margin - maintenance_margin_requirement - (position_size * asset_price)) / position_size
        else:
            liquidation_price = (available_margin - maintenance_margin_requirement + (position_size * asset_price)) / position_size

        if liquidation_price <= 0:
            logger.error(f"SynthetixPositionControllerUtils - Calculated invalid liquidation price: {liquidation_price}.")
            return None

        logger.info(f"SynthetixPositionControllerUtils - Liquidation price calculated successfully: {liquidation_price}")
        return liquidation_price

    except KeyError as ke:
        logger.error(f"SynthetixPositionControllerUtils - Key error in input data during liquidation price calculation: {ke}. Data might be incomplete.")
        return None
    except Exception as e:
        logger.error(f"SynthetixPositionControllerUtils - Unexpected error during liquidation price calculation: {e}")
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
from decimal import Decimal, DecimalException
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

def calculate_liquidation_price(position_data, asset_price: float) -> float:
    try:
        position = position_data['position']
        margin_info = position_data['margin_info']
        current_asset_price = Decimal(asset_price)

        position_size = Decimal(str(position['position_size']))
        available_margin = Decimal(str(margin_info['available_margin']))
        maintenance_margin_requirement = Decimal(str(margin_info['maintenance_margin_requirement']))
        initial_margin_requirement = Decimal(str(margin_info['initial_margin_requirement']))

        if initial_margin_requirement > 0:
            maintenance_margin_ratio = maintenance_margin_requirement / initial_margin_requirement
        else:
            maintenance_margin_ratio = Decimal('0.5')

        bankruptcy_price = available_margin / (position_size * maintenance_margin_ratio * current_asset_price)
        liquidation_price = current_asset_price + (bankruptcy_price - current_asset_price) / Decimal('1.05')

        return float(liquidation_price)
    except KeyError as e:
        logger.error(f"SynthetixPositionMonitorUtils - Key error in calculating liquidation price: {e}")
    except DecimalException as e:
        logger.error(f"SynthetixPositionMonitorUtils - Decimal operation error in calculating liquidation price: {e}")
    except Exception as e:
        logger.error(f"SynthetixPositionMonitorUtils - Unexpected error in calculating liquidation price: {e}")

    return float('nan')

def get_side(size: float) -> str:
    try:
        if size > 0:
            return 'Long'
        elif size < 0:
            return 'Short'
    except Exception as e:
        logger.error(f"SynthetixPositionMonitorUtils - Error determining side from size {size}: {e}")
        return 'Error'
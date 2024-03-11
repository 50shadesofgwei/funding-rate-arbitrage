from decimal import Decimal
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

def calculate_liquidation_price(position_data) -> float:
    position = position_data['position']
    margin_info = position_data['margin_info']
    current_asset_price = position_data['symbol']

    position_size = Decimal(str(position['position_size']))
    available_margin = Decimal(str(margin_info['available_margin']))
    maintenance_margin_requirement = Decimal(str(margin_info['maintenance_margin_requirement']))
    initial_margin_requirement = Decimal(str(margin_info['initial_margin_requirement']))

    if initial_margin_requirement > 0:
        maintenance_margin_ratio = maintenance_margin_requirement / initial_margin_requirement
    else:
        maintenance_margin_ratio = Decimal('0.5')

    bankruptcy_price = available_margin / (position_size * maintenance_margin_ratio * Decimal(str(current_asset_price)))
    liquidation_price = current_asset_price + (bankruptcy_price - current_asset_price) / Decimal('1.05')

    return float(liquidation_price)

def get_side(size: float) -> str:
    try:
        if size > 0:
            return 'Long'
        elif size < 0:
            return 'Short'
    except Exception as e:
        logger.error(f"SynthetixPositionMonitorUtils - Error determining side from size {size}: {e}")
        return 'Error'
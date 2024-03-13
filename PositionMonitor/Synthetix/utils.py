from decimal import Decimal, DecimalException
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

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
        if initial_margin_requirement <= 0 or position_size == 0 or current_asset_price == 0:
            logger.error("Initial margin requirement, position size, or current asset price is zero, cannot calculate liquidation price.")
            return float('nan')

        maintenance_margin_ratio = maintenance_margin_requirement / initial_margin_requirement if initial_margin_requirement > 0 else Decimal('0.5')

        # Calculate bankruptcy price, ensuring divisor is not zero
        divisor = (position_size * maintenance_margin_ratio * current_asset_price)
        if divisor == 0:
            logger.error("Division by zero encountered in bankruptcy price calculation.")
            return float('nan')

        bankruptcy_price = available_margin / divisor
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
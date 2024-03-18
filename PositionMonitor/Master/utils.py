from enum import Enum
from GlobalUtils.logger import logger

class PositionCloseReason(Enum):
    LIQUIDATION_RISK = "LIQUIDATION_RISK"
    FOUND_BETTER_OPPORTUNITY = "FOUND_BETTER_OPPORTUNITY"
    NO_LONGER_PROFITABLE = "NO_LONGER_PROFITABLE"
    POSITION_OPEN_ERROR = "POSITION_OPEN_ERROR"
    
def get_dict_from_database_response(response):
    columns = [
        'id', 'strategy_execution_id', 'order_id', 'exchange', 'symbol',
        'side', 'size', 'open_close', 'open_time', 'close_time',
        'pnl', 'position_delta', 'close_reason'
    ]
    response_dict = {columns[i]: response[i] for i in range(len(columns))}

    return response_dict

def calculate_funding_impact(position, funding_rate: float) -> float:
        """Calculate the dollar impact of the funding rate on the position."""
        try:
            if not isinstance(position, dict):
                raise ValueError("Position must be a dictionary.")
            if not isinstance(funding_rate, float):
                raise ValueError("Funding rate must be a float.")
            if 'size' not in position or 'side' not in position:
                raise KeyError("Missing 'size' or 'side' in position data.")
            
            size = position.get('size', 0)
            if not isinstance(size, (int, float)) or size <= 0:
                raise ValueError("Position size must be a positive number.")
            
            side = position.get('side', '').upper()
            if side not in ['LONG', 'SHORT']:
                raise ValueError("Position side must be 'LONG' or 'SHORT'.")

            impact_multiplier = 1 if side == 'LONG' else -1
            funding_impact = funding_rate * size * impact_multiplier
            return funding_impact

        except (ValueError, KeyError) as e:
            logger.error(f"Error calculating funding impact: {e}")
            return 0.0

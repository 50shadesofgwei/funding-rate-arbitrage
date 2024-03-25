from enum import Enum
from GlobalUtils.logger import logger

class PositionCloseReason(Enum):
    LIQUIDATION_RISK = "LIQUIDATION_RISK"
    FOUND_BETTER_OPPORTUNITY = "FOUND_BETTER_OPPORTUNITY"
    NO_LONGER_PROFITABLE = "NO_LONGER_PROFITABLE"
    DELTA_ABOVE_BOUND = "DELTA_ABOVE_BOUND"
    POSITION_OPEN_ERROR = "POSITION_OPEN_ERROR"
    TEST = "TEST"
    
def get_dict_from_database_response(response):
    columns = [
        'id', 'strategy_execution_id', 'order_id', 'exchange', 'symbol',
        'side', 'size', 'liquidation_price', 'open_close', 'open_time', 
        'close_time', 'pnl', 'accrued_funding', 'close_reason'
    ]
    response_dict = {columns[i]: response[i] for i in range(len(columns))}

    return response_dict


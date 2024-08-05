import os
from GlobalUtils.logger import logger
from dotenv import load_dotenv
load_dotenv()

def get_side(is_long: bool) -> str:
        if is_long:
            side = 'Buy'
            return side
        else:
            side = 'Sell'
            return side

def get_opposite_side(side: str) -> str:
    try:
        if side == 'Buy' or side == 'Sell':
            if side == 'Buy':
                opposite_side = 'Sell'
            elif side == 'Sell':
                opposite_side = 'Buy'
            return opposite_side
        else:
            logger.error(f"ByBitPositionControllerUtils - get_opposite_side called with an argument that is neither 'Buy' nor 'Sell', arg = {side}.")
            return None
    except Exception as e:
            logger.error(f"ByBitPositionControllerUtils - Failed to get opposite side for input: {side}. Error: {e}")
            return None


def is_leverage_already_correct(leverage_factor: float) -> bool:
    system_leverage = float(os.getenv('TRADE_LEVERAGE'))
    if system_leverage == leverage_factor:
        return True
    else:
        return False

def parse_close_order_data_from_position_response(APIresponse: dict) -> dict:
    symbol = APIresponse['result']['list'][0]['symbol']
    side = APIresponse['result']['list'][0]['side']
    size = APIresponse['result']['list'][0]['size']
    opposite_side = get_opposite_side(side)
    
    close_order = {
        'symbol': symbol,
        'side': opposite_side,
        'size': size
    }

    return close_order

def normalize_qty_step(qty_step: float) -> int:
    decimal_str = str(qty_step)
    if '.' in decimal_str:
        return len(decimal_str.split('.')[1])
    else:
        return 0
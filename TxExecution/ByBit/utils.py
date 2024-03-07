import os
from dotenv import load_dotenv
load_dotenv()

def get_side(is_long: bool) -> str:
        if is_long:
            side = 'Buy'
            return side
        else:
            side = 'Sell'
            return side

def is_leverage_already_correct(leverage_factor: float) -> bool:
    system_leverage = float(os.getenv('TRADE_LEVERAGE'))
    if system_leverage == leverage_factor:
        return True
    else:
        return False
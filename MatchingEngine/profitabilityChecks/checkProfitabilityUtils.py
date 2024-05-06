from GlobalUtils.logger import logger

def get_adjusted_size(size: float, is_long: bool) -> float:
    try:
        if not is_long:
            trade_effect = -1 
            size = size * trade_effect
            return size
        else: 
            return size
    except Exception as e:
        logger.error(f'CheckProfitabilityUtils - Error while calculating adjusted trade size for size {size}, is_long = {is_long}: {e}')
        return None
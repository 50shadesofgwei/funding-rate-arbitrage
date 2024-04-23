from GlobalUtils.logger import logger

def calculate_open_interest_differential_usd(ratio: float, open_interest: float, price: float) -> float:
    try:
        total_parts = ratio + 1
        long_ratio = ratio / total_parts
        short_ratio = 1 / total_parts
        long_value = long_ratio * open_interest * price
        short_value = short_ratio * open_interest * price

        differential = abs(long_value - short_value)

        return differential
    except TypeError:
        logger.info("BinanceBacktesterUtils - Invalid input types: ratio, open_interest, and price must be numbers.")
    except Exception as e:
        logger.info(f"BinanceBacktesterUtils - An error occurred: {e}")
    return 0.0

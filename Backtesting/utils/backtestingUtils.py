

def calculate_effective_apr(funding_rate: float) -> float:
    apr = funding_rate * 3 * 365
    return apr

BOUND_CONST = 0.68
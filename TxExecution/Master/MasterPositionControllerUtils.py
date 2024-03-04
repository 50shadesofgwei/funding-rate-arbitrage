

def check_other_exchange_has_adequate_collateral(collateral_amounts, exchange: str, desired_collateral_amount: float) -> bool:
    collateral = collateral_amounts.get(exchange, 0)
    return collateral >= desired_collateral_amount

def adjust_collateral_allocation(collateral_amounts, long_exchange, short_exchange, initial_percentage=75, decrement=10, attempts=3):
    max_collateral = get_max_collateral_from_selected_exchanges(collateral_amounts, long_exchange, short_exchange)
    desired_collateral = max_collateral * (initial_percentage / 100)

    for _ in range(attempts):
        if check_other_exchange_has_adequate_collateral(collateral_amounts, short_exchange, desired_collateral):
            return desired_collateral
        else:
            desired_collateral *= (1 - decrement / 100)

    raise ValueError(f"Not enough capital on {short_exchange} for the trade.")

def get_max_collateral_from_selected_exchanges(collateral_amounts, primary_exchange, secondary_exchange):
    return max(collateral_amounts.get(primary_exchange, 0), collateral_amounts.get(secondary_exchange, 0))



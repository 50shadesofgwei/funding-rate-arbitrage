from GlobalUtils.globalUtils import *

def group_by_symbol(funding_rates):
    """Group funding rates by normalized symbol."""
    rates_by_symbol = {}
    for entry in funding_rates:
        symbol = normalize_symbol(entry['symbol'])
        rates_by_symbol.setdefault(symbol, []).append(entry)
    return rates_by_symbol

def sort_funding_rates_by_value(rates):
    """Sort funding rates for each symbol by the funding rate value."""
    return sorted(rates, key=lambda x: float(x['funding_rate']))
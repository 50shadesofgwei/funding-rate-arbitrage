from GlobalUtils.globalUtils import *

def group_by_symbol(funding_rates):
    rates_by_symbol = {}
    for entry in funding_rates:
        symbol = normalize_symbol(entry['symbol'])
        rates_by_symbol.setdefault(symbol, []).append(entry)
    return rates_by_symbol

def sort_funding_rates_by_value(rates):
    return sorted(rates, key=lambda x: float(x['funding_rate']))
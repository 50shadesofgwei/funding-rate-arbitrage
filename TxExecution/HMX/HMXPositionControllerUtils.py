from hmx2.constants.markets import *
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import get_price_from_pyth

def get_market_for_symbol(symbol: str):
    asset_mapping = {
        'BTC': ARBITRUM_MARKET_BTC_USD,
        'ETH': ARBITRUM_MARKET_ETH_USD,
        'SOL': ARBITRUM_MARKET_SOL_USD,
        'W': ARBITRUM_MARKET_W_USD,
        'ENA': ARBITRUM_MARKET_ENA_USD,
        'DOGE': ARBITRUM_MARKET_DOGE_USD,
        'PEPE': ARBITRUM_MARKET_1000PEPE_USD,
        'ARB': ARBITRUM_MARKET_ARB_USD,
        'BNB': ARBITRUM_MARKET_BNB_USD
    }

    market = asset_mapping.get(symbol)
    if market is None:
        logger.error(f"HMXPositionControllerUtils - No market found for symbol: {symbol}")
        return None
    return market

def get_symbol_for_market(market: int):
    asset_mapping = {
        ARBITRUM_MARKET_BTC_USD: 'BTC',
        ARBITRUM_MARKET_ETH_USD: 'ETH',
        ARBITRUM_MARKET_SOL_USD: 'SOL',
        ARBITRUM_MARKET_W_USD: 'W',
        ARBITRUM_MARKET_ENA_USD: 'ENA',
        ARBITRUM_MARKET_DOGE_USD: 'DOGE',
        ARBITRUM_MARKET_1000PEPE_USD: 'PEPE',
        ARBITRUM_MARKET_ARB_USD: 'ARB',
        ARBITRUM_MARKET_BNB_USD: 'BNB',
    }

    market = asset_mapping.get(market)
    if market is None:
        logger.error(f"HMXPositionControllerUtils - No symbol found for market: {market}")
        return None
    return market

def get_position_size_from_response(response: dict, entry_price: float) -> float:
    try:
        size_delta = response['order']['sizeDelta']
        size_usd = size_delta/10**30
        size = round(entry_price / size_usd, 3)
        return size
    except Exception as e:
        logger.error(f'HMXPositionControllerUtils - Failed to calculate position size from response. Entry price={entry_price}, Error: {e}')
        return None

def is_long(size: float) -> bool:
    if size > 0:
        return True
    elif size < 0:
        return False
    else:
        return None

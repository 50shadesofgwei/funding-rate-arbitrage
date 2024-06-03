from hmx2.constants.markets import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *

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

@log_function_call
def calculate_liquidation_price(position_data: dict, asset_price: float) -> float:
    try:
        position_size = position_data['position']['position_size']
        available_margin = position_data['margin_details']['available_margin']
        maintenance_margin_requirement = position_data['margin_details']['maintenance_margin_requirement']

        logger.info(f"HMXPositionControllerUtils - Calculating liquidation price with position_size={position_size}, available_margin={available_margin}, maintenance_margin_requirement={maintenance_margin_requirement}, asset_price={asset_price}")

        if not position_size:
            logger.error(f"HMXPositionControllerUtils - Invalid position size: {position_size}. Cannot calculate liquidation price.")
            return None
        if asset_price <= 0:
            logger.error(f"HMXPositionControllerUtils - Invalid asset price: {asset_price}. Cannot calculate liquidation price.")
            return None
        if available_margin <= 0 or maintenance_margin_requirement < 0:
            logger.error(f"HMXPositionControllerUtils - Invalid margin values: Available={available_margin}, Maintenance Requirement={maintenance_margin_requirement}.")
            return None

        is_long = position_size > 0
        if is_long:
            liquidation_price = (available_margin - maintenance_margin_requirement - (position_size * asset_price)) / position_size
        else:
            liquidation_price = (available_margin - maintenance_margin_requirement + (position_size * asset_price)) / position_size

        if liquidation_price <= 0:
            logger.error(f"HMXPositionControllerUtils - Calculated invalid liquidation price: {liquidation_price}.")
            return None

        logger.info(f"HMXPositionControllerUtils - Liquidation price calculated successfully: {liquidation_price}")
        return liquidation_price

    except KeyError as ke:
        logger.error(f"HMXPositionControllerUtils - Key error in input data during liquidation price calculation: {ke}. Data might be incomplete.")
        return None
    except Exception as e:
        logger.error(f"HMXPositionControllerUtils - Unexpected error during liquidation price calculation: {e}")
        return None
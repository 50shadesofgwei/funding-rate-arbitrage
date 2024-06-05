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
        size = round(size_usd / entry_price, 3)
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
def calculate_liquidation_price(params: dict) -> float:
    try:
        logger.info(f"HMXPositionControllerUtils - Calculating liquidation price with parameters: {params}")

        if not params["position_size"]:
            logger.error("HMXPositionControllerUtils - Invalid position size: Cannot calculate liquidation price.")
            return None
        if params["asset_price"] <= 0:
            logger.error("HMXPositionControllerUtils - Invalid asset price: Cannot calculate liquidation price.")
            return None
        if params["available_margin"] <= 0 or params["maintenance_margin_requirement"] < 0:
            logger.error("HMXPositionControllerUtils - Invalid margin values: Available or Maintenance Requirement.")
            return None

        base_calculation = float(params["available_margin"]) - float(params["maintenance_margin_requirement"])
        price_component = float(params["position_size"]) * float(params["asset_price"])
        liquidation_price = (base_calculation - price_component) if params["is_long"] else (base_calculation + price_component)
        liquidation_price /= params["position_size"]
        liquidation_price = abs(liquidation_price)

        if liquidation_price <= 0:
            logger.error(f"HMXPositionControllerUtils - Calculated invalid liquidation price: {liquidation_price}.")
            return None

        return liquidation_price

    except KeyError as ke:
        logger.error(f"HMXPositionControllerUtils - Key error in input data: {ke}. Data might be incomplete.")
        return None
    except Exception as e:
        logger.error(f"HMXPositionControllerUtils - Unexpected error during calculation: {e}")
        return None

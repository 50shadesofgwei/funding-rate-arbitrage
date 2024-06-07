from hmx2.constants.markets import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
import sqlite3

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
        'BNB': ARBITRUM_MARKET_BNB_USD,
        'AVAX': ARBITRUM_MARKET_AVAX_USD,
        'PENDLE': ARBITRUM_MARKET_PENDLE_USD
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
        ARBITRUM_MARKET_AVAX_USD: 'AVAX',
        ARBITRUM_MARKET_PENDLE_USD: 'PENDLE'
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

def calculate_liquidation_price(params: dict) -> float:
    try:
        logger.info(f"Calculating liquidation price with parameters: {params}")

        if params["size_usd"] <= 0 or params["asset_price"] <= 0:
            logger.error("Invalid size or asset price for liquidation calculation.")
            return None

        if params["available_margin"] <= 0:
            logger.error("Invalid available margin for liquidation calculation.")
            return None

        maintenance_margin_percent = float(params["maintenance_margin_requirement"]) / 10000
        maintenance_margin_amount = params["size_usd"] * params["asset_price"] * maintenance_margin_percent

        if params["is_long"]:
            price_decrease_needed = (params["available_margin"] - maintenance_margin_amount) / params["size_usd"]
            liquidation_price = params["asset_price"] - price_decrease_needed
        else:
            price_increase_needed = (params["available_margin"] + maintenance_margin_amount) / abs(params["size_usd"])
            liquidation_price = params["asset_price"] + price_increase_needed

        liquidation_price = abs(liquidation_price)

        if liquidation_price <= 0:
            logger.error(f"Calculated invalid liquidation price: {liquidation_price}")
            return None

        logger.info(f"Liquidation price calculated successfully: {liquidation_price}")
        return liquidation_price

    except Exception as e:
        logger.error(f"Error during liquidation price calculation: {e}")
        return None

def get_side_for_open_trade_from_database(symbol: str) -> bool:
    try:
        with sqlite3.connect('trades.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT side FROM trade_log WHERE open_close = 'Open' AND exchange = 'HMX' AND symbol = ? LIMIT 1;", (symbol,))
            open_position = cursor.fetchone()
            if open_position:
                return open_position[0].lower() == 'long'
            else:
                logger.info(f"No open positions found for symbol: {symbol}")
                return False
    except Exception as e:
        logger.error(f"HMXPositionMonitor - Error while searching for open HMX positions: {e}")
        return None



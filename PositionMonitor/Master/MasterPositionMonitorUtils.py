from enum import Enum
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
import sqlite3

class PositionCloseReason(Enum):
    LIQUIDATION_RISK = "LIQUIDATION_RISK"
    FOUND_BETTER_OPPORTUNITY = "FOUND_BETTER_OPPORTUNITY"
    NO_LONGER_PROFITABLE = "NO_LONGER_PROFITABLE"
    DELTA_ABOVE_BOUND = "DELTA_ABOVE_BOUND"
    POSITION_OPEN_ERROR = "POSITION_OPEN_ERROR"
    FUNDING_TURNING_AGAINST_TRADE = "FUNDING_TURNING_AGAINST_TRADE"
    CLOSE_ALL_POSITIONS = "CLOSE_ALL_POSITIONS"
    TEST = "TEST"
    
def get_dict_from_database_response(response):
    columns = [
        'id', 'strategy_execution_id', 'exchange', 'symbol',
        'side', 'size', 'liquidation_price', 'open_close', 'open_time', 
        'close_time', 'pnl', 'accrued_funding', 'close_reason'
    ]
    response_dict = {columns[i]: response[i] for i in range(len(columns))}

    return response_dict

def get_percentage_away_from_liquidation_price(position: dict) -> float:
        try:
            liquidation_price = float(position['liquidation_price'])
            symbol = str(position['symbol'])
            normalized_symbol = normalize_symbol(symbol)
            asset_price = get_price_from_pyth(normalized_symbol)
            is_long = float(position['size']) > 0
            differential = float(asset_price-liquidation_price) if is_long else float(liquidation_price-asset_price)
            percentage: float = asset_price / differential
            return percentage

        except Exception as e:
            logger.error(f"MasterPositionMonitorUtils - Error checking for percentage away from liquidation price for {symbol}: {e}")
            return None

def is_open_position_for_symbol_on_exchange(symbol: str, exchange: str) -> bool:
        try:
            with sqlite3.connect('trades.db') as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT 1
                    FROM trade_log
                    WHERE open_close = 'Open' 
                      AND symbol = ?
                      AND exchange = ?;
                '''
                
                cursor.execute(sql_query, (symbol, exchange))
                open_positions = cursor.fetchone()
                
                return open_positions is not None

        except Exception as e:
            logger.error(f"MasterPositionMonitorUtils - Error while searching for open positions for {symbol} on exchange {exchange}. Error: {e}")
            return None

def get_open_position_for_exchange(exchange: str) -> dict:
        try:
            with sqlite3.connect('trades.db') as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT 1
                    FROM trade_log 
                    WHERE open_close = 'Open' 
                      AND exchange = ?;
                '''
                
                cursor.execute(sql_query, (exchange))
                open_position = cursor.fetchone()
                
                if open_position:
                    position_dict = get_dict_from_database_response(open_position)
                    return position_dict
                else:
                    return None
        except Exception as e:
            logger.error(f"MasterPositionMonitorUtils - Error while searching for open Binance positions: {e}")
            return None

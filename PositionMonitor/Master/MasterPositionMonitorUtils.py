from enum import Enum
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from APICaller.Synthetix.SynthetixUtils import GLOBAL_SYNTHETIX_CLIENT
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
    try:
        columns = [
            'id', 'strategy_execution_id', 'exchange', 'symbol',
            'side', 'is_hedge', 'size_in_asset', 'liquidation_price', 'open_close', 'open_time', 
            'close_time', 'pnl', 'accrued_funding', 'close_reason'
        ]

        response_list = list(response) if isinstance(response, tuple) else response
        if len(response_list) < len(columns):
            response_list.extend([None] * (len(columns) - len(response_list)))

        response_dict = {columns[i]: response_list[i] for i in range(len(columns))}

        return response_dict

    except Exception as e:
        logger.error(f'MasterPositionMonitorUtils - Error parsing dict from database response. Error: {e}')
        return None


def get_percentage_away_from_liquidation_price(position: dict) -> float:
    try:
        symbol = position.get('symbol', 'Unknown Symbol')
        liquidation_price = float(position['liquidation_price'])
        normalized_symbol = normalize_symbol(symbol)
        asset_price = get_price_from_pyth(normalized_symbol, GLOBAL_SYNTHETIX_CLIENT)

        is_long = position['side'].lower() == 'long'
        differential = asset_price - liquidation_price if is_long else liquidation_price - asset_price

        if asset_price > 0:
            percentage = abs(differential / asset_price) * 100
        else:
            logger.error(f"MasterPositionMonitorUtils - Current asset price is zero or negative: {asset_price}")
            return None

        logger.info(f'MasterPositionMonitorUtils - Percentage away from liquidation = {percentage}% for {symbol}')
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
                    SELECT id, strategy_execution_id, exchange, symbol,
                    side, is_hedge, size_in_asset, liquidation_price, open_close, open_time, 
                    close_time, pnl, accrued_funding, close_reason
                    FROM trade_log 
                    WHERE open_close = 'Open' 
                    AND exchange = ?;
                '''
                
                cursor.execute(sql_query, (exchange,))
                open_position = cursor.fetchone()
                
                if open_position:
                    position_dict = get_dict_from_database_response(open_position)
                    return position_dict
                else:
                    return None

        except sqlite3.Error as sqe:
            logger.error(f"MasterPositionMonitorUtils - SQL Error while searching for open position for exchange {exchange}: {sqe}")
            return None

        except Exception as e:
            logger.error(f"MasterPositionMonitorUtils - Error while searching for open position for exchange {exchange}: {e}")
            return None

from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from binance.enums import *
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class BinancePositionMonitor():
    def __init__(self, db_path='trades.db'):
        self.client = GLOBAL_BINANCE_CLIENT
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error accessing the database: {e}")
            raise e

    def get_open_position(self) -> dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT * 
                    FROM trade_log 
                    WHERE open_close = 'Open' 
                      AND exchange = 'Binance';
                '''
                
                cursor.execute(sql_query, ())
                open_positions = cursor.fetchall()
                
                if open_positions:
                    position_dict = get_dict_from_database_response(open_positions[0])
                    return position_dict
                else:
                    logger.info("BinancePositionMonitor - No open Binance positions found")
                    return None
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions: {e}")
            return None

    def is_near_liquidation_price(self, position) -> bool:
        try:
            liquidation_price = float(position['liquidation_price'])
            symbol = position['symbol']
            
            normalized_symbol = normalize_symbol(symbol)
            asset_price = get_price_from_pyth(normalized_symbol)

            lower_bound = liquidation_price * 0.9
            upper_bound = liquidation_price * 1.1

            if lower_bound <= asset_price <= upper_bound:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error checking if near liquidation price for {symbol}: {e}")
            return False

    def get_funding_rate(self, position) -> float:
        try:
            symbol = position['symbol']
            funding_rate = self.client.funding_rate(symbol=symbol)
            latest_funding_data = funding_rate[-1]
            latest_funding_data_as_float = float(latest_funding_data.get('fundingRate'))
            if funding_rate and len(funding_rate) > 0:
                return latest_funding_data_as_float

        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error fetching funding rate for symbol {symbol}: {e}")
            return 0.0

    def is_open_position(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT 1
                    FROM trade_log
                    WHERE open_close = 'Open' 
                      AND exchange = 'Binance';
                '''
                
                cursor.execute(sql_query, ())
                open_positions = cursor.fetchall()
                
                return open_positions is not None

        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions: {e}")
            return None

    def is_open_position_for_symbol(self, symbol: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT 1
                    FROM trade_log
                    WHERE open_close = 'Open' 
                      AND symbol = ?
                      AND exchange = 'Binance';
                '''
                
                cursor.execute(sql_query, (symbol,))
                open_positions = cursor.fetchone()
                
                return open_positions is not None

        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions for {symbol}: {e}")
            return None
        







    
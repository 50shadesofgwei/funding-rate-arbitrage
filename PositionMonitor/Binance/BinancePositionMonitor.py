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

    def is_near_liquidation_price(self, position: dict) -> bool:
        try:
            percentage_from_liqiudation_price = get_percentage_away_from_liquidation_price(position)
            if percentage_from_liqiudation_price > float(os.getenv('MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE')):
                return True

        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error checking if near liquidation price for {position}: {e}")
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


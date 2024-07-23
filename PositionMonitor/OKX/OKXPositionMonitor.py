from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from APICaller.OKX.okxUtils import set_okx_symbol
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class OKXPositionMonitor():
    def __init__(self, db_path='trades.db'):
        self.client = GLOBAL_OKX_PUBLIC_CLIENT
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"OKXPositionMonitor - Error accessing the database: {e}")
            return None



    def is_near_liquidation_price(self, position: dict) -> bool:
        try:
            percentage_from_liqiudation_price = get_percentage_away_from_liquidation_price(position)
            if percentage_from_liqiudation_price > float(os.getenv('MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE')):
                return True

        except Exception as e:
            logger.error(f"OKXPositionMonitor - Error checking if near liquidation price for {position}: {e}")
            return False

    def get_funding_rate(self, position) -> float:
        try:
            symbol = position['symbol']
            okx_symbol = set_okx_symbol(symbol)
            response = self.client.get_funding_rate(instId=okx_symbol)
            funding_rate = float(response['data'][0]['fundingRate'])
            if funding_rate and len(funding_rate) > 0:
                return funding_rate
        except Exception as e:
            logger.error(f"OKXPositionMonitor - Error fetching funding rate for symbol {symbol}: {e}")
            return 0.0

    def is_open_position(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT 1
                    FROM trade_log
                    WHERE open_close = 'Open' 
                      AND exchange = 'OKX';
                '''
                
                cursor.execute(sql_query, ())
                open_positions = cursor.fetchall()
                
                return open_positions is not None

        except Exception as e:
            logger.error(f"OKXPositionMonitor - Error while searching for open OKX positions: {e}")
            return None


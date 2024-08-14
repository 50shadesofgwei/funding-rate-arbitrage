from PositionMonitor.Master.MasterPositionMonitorUtils import *
from APICaller.ByBit.ByBitCaller import GLOBAL_BYBIT_CLIENT
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class ByBitPositionMonitor():
    def __init__(self, db_path='trades.db'):
        self.client = GLOBAL_BYBIT_CLIENT
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"ByBitPositionMonitor - Error accessing the database: {e}")
            return None

    def is_near_liquidation_price(self, position: dict) -> bool:
        try:
            percentage_from_liqiudation_price = get_percentage_away_from_liquidation_price(position)
            if percentage_from_liqiudation_price < float(os.getenv('MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE')):
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"ByBitPositionMonitor - Error checking if near liquidation price for {position}: {e}")
            return False

    def get_funding_rate(self, position) -> float:
        try:
            symbol = position['symbol']
            response = self.client.get_tickers(
                category='linear',
                symbol=symbol+'USDT',
                limit='1',
                fundingInterval='1'
            )
            if response and response.get('retCode') == 0 and 'result' in response and 'list' in response['result']:
                return float(response['result']['list'][0]['fundingRate'])
                
            else:
                return None
        except Exception as e:
            logger.error(f"ByBitPositionMonitor - Failed to fetch funding rate data for {symbol} from API. Error: {e}")
            return None

    def is_open_position(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                sql_query = '''
                    SELECT 1
                    FROM trade_log
                    WHERE open_close = 'Open' 
                      AND exchange = 'ByBit';
                '''
                
                cursor.execute(sql_query, ())
                open_positions = cursor.fetchall()
                
                return open_positions is not None

        except Exception as e:
            logger.error(f"ByBitPositionMonitor - Error while searching for open Binance positions: {e}")
            return None
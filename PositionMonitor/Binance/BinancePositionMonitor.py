import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.Binance.binanceUtils import BinanceEnvVars
from PositionMonitor.Binance.utils import *
from GlobalUtils.logger import logger
from binance.um_futures import UMFutures as Client
from binance.enums import *
from pubsub import pub
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class BinancePositionMonitor():
    def __init__(self, db_path='trades.db'):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret, base_url="https://testnet.binancefuture.com")
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error accessing the database: {e}")
            raise e

    def get_open_position_from_strategy_id(self, strategy_execution_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trade_log WHERE strategy_execution_id = ? AND status = 'OPEN' AND exchange = 'Binance';''', (strategy_execution_id,))
            open_positions = cursor.fetchall()
            if open_positions:
                position_dict = get_dict_from_database_response(open_positions[0])
                return position_dict
            else:
                logger.info(f"BinancePositionMonitor - No open positions found for strategy_execution_id {strategy_execution_id}")
                return None
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open positions for strategy_execution_id {strategy_execution_id}:", {e})
            raise e

    def is_near_liquidation_price(self, position):
        pass



    
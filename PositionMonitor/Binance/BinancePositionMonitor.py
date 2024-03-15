import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.Binance.binanceUtils import BinanceEnvVars
from PositionMonitor.Binance.utils import *
from PositionMonitor.Master.utils import *
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
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
        self.close_reason = PositionCloseReason()
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error accessing the database: {e}")
            raise e

    def position_health_check(self):
        try:
            if self.is_open_position():
                position = self.get_open_position()
                if self.is_near_liquidation_price(position):
                    reason = self.close_reason.LIQUIDATION_RISK
                    pub.sendMessage('close_positions', reason)
                else:
                    return
            else:
                return
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error checking position health: {e}")
            raise e


    def get_open_position(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trade_log WHERE status = 'OPEN' AND exchange = 'Binance';''')
            open_positions = cursor.fetchall()
            if open_positions:
                position_dict = get_dict_from_database_response(open_positions[0])
                return position_dict
            else:
                logger.info(f"BinancePositionMonitor - No open Binance positions found")
                return None
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions:", {e})
            raise e

    def is_near_liquidation_price(self, position) -> bool:
        try:
            liquidation_price = float(position['liquidation_price'])
            symbol = position['symbol']
            
            # Assume these functions are defined elsewhere in your code
            normalized_symbol = normalize_symbol(symbol)
            full_symbol = get_full_asset_name(normalized_symbol)
            asset_price = get_asset_price(full_symbol)

            # Calculate the 10% threshold range
            lower_bound = liquidation_price * 0.9
            upper_bound = liquidation_price * 1.1

            # Check if the asset price is within 10% of the liquidation price
            if lower_bound <= asset_price <= upper_bound:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error checking if near liquidation price for {symbol}: {e}")
            return False

    def is_open_position(self) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trade_log WHERE status = 'OPEN' AND exchange = 'Binance';''')
            open_positions = cursor.fetchall()
            if open_positions:
                return True
            else:
                 return False
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions:", {e})
            raise e
        







    
import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.Binance.binanceUtils import BinanceEnvVars
from PositionMonitor.Binance.utils import *
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.logger import *
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
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error accessing the database: {e}")
            raise e

    @log_function_call
    def get_open_position(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM trade_log WHERE open_close = 'Open' AND exchange = 'Binance';''')
                open_positions = cursor.fetchall()
                if open_positions:
                    position_dict = get_dict_from_database_response(open_positions[0])
                    logger.info(f'BinancePositionMonitor - Open trade pulled from database: {position_dict}')
                    return position_dict
                else:
                    logger.info(f"BinancePositionMonitor - No open Binance positions found")
                    return None
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions:", {e})
            raise e

    @log_function_call
    def is_near_liquidation_price(self, position) -> bool:
        try:
            liquidation_price = float(position['liquidation_price'])
            symbol = position['symbol']
            
            normalized_symbol = normalize_symbol(symbol)
            full_symbol = get_full_asset_name(normalized_symbol)
            asset_price = get_asset_price(full_symbol)

            lower_bound = liquidation_price * 0.9
            upper_bound = liquidation_price * 1.1

            if lower_bound <= asset_price <= upper_bound:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error checking if near liquidation price for {symbol}: {e}")
            return False

    @log_function_call
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

    @log_function_call
    def is_open_position(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM trade_log WHERE open_close = 'Open' AND exchange = 'Binance';''')
                open_positions = cursor.fetchall()
                if open_positions:
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"BinancePositionMonitor - Error while searching for open Binance positions:", {e})
            raise e
        







    
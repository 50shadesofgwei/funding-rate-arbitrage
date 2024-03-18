import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from pubsub import pub
from decimal import Decimal
from PositionMonitor.Synthetix.utils import *
from PositionMonitor.Master.utils import *
import sqlite3
import uuid

class SynthetixPositionMonitor():
    def __init__(self, db_path='trades.db'):
        self.client = get_synthetix_client()
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"SynthetixPositionMonitor - Error accessing the database: {e}")
            raise e

    def position_health_check(self):
        try:
            if self.is_open_position():
                position = self.get_open_position()
                if self.is_near_liquidation_price(position):
                    reason = PositionCloseReason.LIQUIDATION_RISK.value
                    pub.sendMessage('close_positions', reason)
                else:
                    return
            else:
                return
        except Exception as e:
            logger.error(f"SynthetixPositionMonitor - Error checking position health: {e}")
            raise e


    def get_open_position(self) -> dict:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trade_log WHERE status = 'OPEN' AND exchange = 'Synthetix';''')
            open_positions = cursor.fetchall()
            if open_positions:
                position_dict = get_dict_from_database_response(open_positions[0])
                return position_dict
            else:
                logger.info(f"SynthetixPositionMonitor - No open Synthetix positions found")
                return None
        except Exception as e:
            logger.error(f"SynthetixPositionMonitor - Error while searching for open Synthetix positions:", {e})
            raise e

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
            logger.error(f"SynthetixPositionMonitor - Error checking if near liquidation price for {symbol}: {e}")
            return False

    def get_funding_rate(self, position) -> float:
        try:
            symbol = position['symbol']
            market = self.client.perps.get_market_summary(market_name=symbol)
            
            if 'current_funding_rate' in market:
                funding_rate = float(market['current_funding_rate'])
                return funding_rate
            else:
                logger.error(f"SynthetixPositionMonitor - Funding rate not found in market summary for symbol {symbol}.")
                return 0.0 
            
        except Exception as e:
            logger.error(f"SynthetixPositionMonitor - Error fetching funding rate for symbol {symbol}: {e}")
            return 0.0

    def is_open_position(self) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trade_log WHERE status = 'OPEN' AND exchange = 'Synthetix';''')
            open_positions = cursor.fetchall()
            if open_positions:
                return True
            else:
                 return False
        except Exception as e:
            logger.error(f"SynthetixPositionMonitor - Error while searching for open Synthetix positions:", {e})
            raise e

    

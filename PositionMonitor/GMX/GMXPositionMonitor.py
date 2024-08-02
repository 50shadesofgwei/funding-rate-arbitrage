from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from APICaller.GMX.GMXContractUtils import *
from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory
import sqlite3

class GMXPositionMonitor():
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(self.db_path)
        except Exception as e:
            logger.error(f"GMXPositionMonitor - Error accessing the database: {e}")
            return None

    def get_open_position(self) -> dict:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM trade_log WHERE open_close = 'Open' AND exchange = 'GMX';''')
                open_position = cursor.fetchone()
                if open_position:
                    position_dict = get_dict_from_database_response(open_position)
                    return position_dict
                else:
                    logger.error("GMXPositionMonitor - No open GMX positions found with details")
                    return None

        except sqlite3.Error as sqe:
            logger.error(f"GMXPositionMonitor - Database error while searching for open GMX positions: {sqe}")
            return None

        except Exception as e:
            logger.error(f"GMXPositionMonitor - Error while searching for open GMX positions: {e}")
            return None


    def is_near_liquidation_price(self, position: dict) -> bool:
        try:
            percentage_from_liqiudation_price = get_percentage_away_from_liquidation_price(position)
            MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE = float(os.getenv('MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE'))
            if percentage_from_liqiudation_price < MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE:
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"GMXPositionMonitor - Error checking if near liquidation price for {position}: {e}")
            return False

    def get_funding_rate(self, position: dict) -> float:
        try:
            symbol = position['symbol']
            market = GMXMarketDirectory.get_market_key_for_symbol(symbol)
            funding_rate_raw = get_funding_factor(market)
            borrow_rate = get_borrow_rate_for_market(market)
            borrow_rate = borrow_rate * -1
            funding_rate_per_second = funding_rate_raw + borrow_rate
            funding_rate_24hr = funding_rate_per_second * 60 * 60 * 24

            return funding_rate_24hr
            
        except Exception as e:
            logger.error(f"GMXPositionMonitor - Error fetching funding rate for symbol {symbol}: {e}")
            return None

    def is_open_position(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM trade_log WHERE open_close = 'Open' AND exchange = 'GMX';''')
                open_positions = cursor.fetchall()
                if open_positions:
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"GMXPositionMonitor - Error while searching for open GMX positions:", {e})
            raise e
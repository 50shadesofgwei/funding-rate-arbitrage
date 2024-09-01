import sqlite3
from datetime import datetime
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from pubsub import pub
import uuid

class TradeLogger:
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        pub.subscribe(self.log_trade_pair, EventsDirectory.POSITION_OPENED.value)
        pub.subscribe(self.log_close_trade, EventsDirectory.POSITION_CLOSED.value)
        try:
            self.conn = self.create_or_access_database()
        except Exception as e:
            logger.error(f"TradeLogger - Error accessing the database: {e}")
            return None

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def create_or_access_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''CREATE TABLE IF NOT EXISTS trade_log (
                        id INTEGER PRIMARY KEY,
                        strategy_execution_id TEXT NOT NULL,
                        exchange TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        is_hedge TEXT NOT NULL,
                        size_in_asset REAL NOT NULL,
                        liquidation_price REAL NOT NULL,
                        open_close TEXT NOT NULL,
                        open_time DATETIME,
                        close_time DATETIME,
                        pnl REAL,
                        accrued_funding REAL,
                        close_reason TEXT
                    );''')
            logger.info("TradeLogger - Database accessed successfully.")
            return conn
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error creating/accessing the database: {e}")
            return None

    def log_trade_pair(self, position_data: dict):
        try:
            strategy_execution_id = str(uuid.uuid4())
            open_time = datetime.now()

            for key in position_data:
                trade = position_data[key]
                exchange = trade['exchange']
                symbol = trade['symbol']
                side = trade['side']
                size = trade['size_in_asset']
                is_hedge = trade['is_hedge']
                liquidation_price = trade['liquidation_price']
                self.log_open_trade(strategy_execution_id, exchange, symbol, side, is_hedge, size, liquidation_price, open_time)
            
            pub.sendMessage(EventsDirectory.TRADE_LOGGED.value, position_data=position_data)

        except KeyError as ke:
            logger.error(f"TradeLogger - KeyError while logging trade pair: {ke}")
            return None

        except Exception as e:
            logger.error(f"TradeLogger - Error logging trade pair: {e}")
            return None


    def log_open_trade(self, strategy_execution_id, exchange, 
                       symbol, side, is_hedge, size, liquidation_price, 
                       open_time=datetime.now()):
        try:
            with sqlite3.connect(self.db_path) as conn:
                sql_query = '''
                    INSERT INTO trade_log (
                        strategy_execution_id, exchange, symbol, 
                        side, is_hedge, size_in_asset, liquidation_price, open_close, open_time
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?);
                '''
                conn.execute(
                    sql_query, 
                    (
                        strategy_execution_id, exchange, symbol, 
                        side, is_hedge, size, liquidation_price, open_time
                    )
                )
                logger.info(f"TradeLogger - Logged open trade for strategy_execution_id: {strategy_execution_id} on exchange: {exchange}")

        except sqlite3.Error as sql_e:
            logger.error(f"TradeLogger - SQL error logging open trade for strategy_execution_id: {strategy_execution_id}, exchange: {exchange}. Error: {sql_e}")
            return None

        except Exception as e:
            logger.error(f"TradeLogger - Error logging open trade for strategy_execution_id: {strategy_execution_id}, exchange: {exchange}. Error: {e}")
            return None

    def log_close_trade(self, position_report: dict):
        try:
            with sqlite3.connect(self.db_path) as conn:
                exchange = position_report['exchange']
                symbol = position_report['symbol']
                execution_id = self.get_open_execution_id(symbol, exchange)
                close_time = datetime.now()
                pnl = position_report['pnl']
                accrued_funding = position_report['accrued_funding']
                close_reason = position_report['reason']

                conn.execute('''UPDATE trade_log 
                                        SET close_time = ?, pnl = ?, accrued_funding = ?, close_reason = ?, open_close = 'Close' 
                                        WHERE strategy_execution_id = ? AND exchange = ?;''', 
                                        (close_time, pnl, accrued_funding, close_reason, execution_id, exchange))
                logger.info(f"TradeLogger - Logged close trade for symbol {symbol} on exchange {exchange} with strategy_execution_id: {execution_id}")

        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error logging closed trade for symbol {symbol} and exchange {exchange} on trade database: Error: {e}")

    def log_close_trade_pair(self, close_reason, strategy_execution_id, position_report: dict):
        try:
            with sqlite3.connect(self.db_path) as conn:
                trades = self.get_trade_pair_by_execution_id(strategy_execution_id)
                if not trades:
                    logger.error(f"TradeLogger - No trades found for strategy_execution_id: {strategy_execution_id}")
                    return

                if len(trades) != 2:
                    logger.error(f"Expected two trades for strategy_execution_id: {strategy_execution_id}, found: {len(trades)}")
                    return

                close_time = datetime.now()
                for trade in trades:
                    exchange = trade[3]
                    pnl = position_report.get(exchange, {}).get('pnl', 0)
                    accrued_funding = position_report.get(exchange, {}).get('accrued_funding', 0)

                    conn.execute('''UPDATE trade_log 
                                        SET close_time = ?, pnl = ?, accrued_funding = ?, close_reason = ?, open_close = 'Close' 
                                        WHERE strategy_execution_id = ? AND exchange = ?;''', 
                                        (close_time, pnl, accrued_funding, close_reason, strategy_execution_id, exchange))
                    logger.info(f"TradeLogger - Logged close trade for {exchange} with strategy_execution_id: {strategy_execution_id}")

        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error logging close trade for strategy_execution_id: {strategy_execution_id}. Error: {e}")
          
    def clear_database(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DROP TABLE IF EXISTS trade_log")
                conn.commit()
                self.create_or_access_database()
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error clearing the database: {e}")

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_trade_pair_by_execution_id(self, strategy_execution_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM trade_log WHERE strategy_execution_id = ?;''', (strategy_execution_id,))
                trades = cursor.fetchall()
                logger.info(f"TradeLogger - Retrieved trades for execution id: {strategy_execution_id}")
                return trades
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error retrieving trades for execution id: {strategy_execution_id}, Error: {e}")
            return []

    def get_open_execution_id(self, symbol: str, exchange: str) -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = """
                        SELECT strategy_execution_id 
                        FROM trade_log 
                        WHERE open_close = 'Open' AND symbol = ? AND exchange = ?
                        GROUP BY strategy_execution_id
                        HAVING COUNT(*) = 1;
                        """
                cursor.execute(query, (symbol, exchange))
                execution_ids = cursor.fetchall()

                if execution_ids:
                    strategy_execution_id = execution_ids[0][0]
                    logger.info(f"TradeLogger - Found open strategy execution ID: {strategy_execution_id}")
                    return str(strategy_execution_id)
                else:
                    logger.error(f"TradeLogger - No open strategy execution ID found for symbol: {symbol} on exchange: {exchange}.")
                    return None
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error retrieving execution ID for open trades. Error: {e}")
            return None

# For UI
    def get_all_trades(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = '''SELECT * FROM trade_log;'''
                cursor.execute(query)
                positions = cursor.fetchall()
                logger.info("TradeLogger - Retrieved all trades.")

                return positions
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error retrieving all trades. Error: {e}")
            return []

        
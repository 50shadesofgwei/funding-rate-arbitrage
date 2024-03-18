import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

import sqlite3
from datetime import datetime
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from pubsub import pub
import uuid

class TradeLogger:
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        pub.subscribe(self.log_trade_pair, eventsDirectory.POSITION_OPENED)
        pub.subscribe(self.log_close_trade, eventsDirectory.POSITION_CLOSED)
        try:
            self.conn = self.create_or_access_database()
        except Exception as e:
            logger.error(f"TradeLogger - Error accessing the database: {e}")
            raise e

    def create_or_access_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''CREATE TABLE IF NOT EXISTS trade_log (
                        id INTEGER PRIMARY KEY,
                        strategy_execution_id TEXT NOT NULL,
                        order_id TEXT NOT NULL,
                        exchange TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        size REAL NOT NULL,
                        liquidation_price REAL NOT NULL,
                        open_close TEXT NOT NULL,
                        open_time DATETIME,
                        close_time DATETIME,
                        pnl REAL,
                        position_delta REAL,
                        close_reason TEXT
                    );''')
            logger.info("TradeLogger - Database accessed successfully.")
            return conn
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error creating/accessing the database: {e}")
            raise e

    def log_trade_pair(self, position_data):
        strategy_execution_id = str(uuid.uuid4())
        open_time = datetime.now()

        for exchange, data in position_data.items():
            print(data)
            order_id = data.get('order_id')
            symbol = data.get('symbol')
            side = data.get('side')
            size = data.get('size')
            self.log_open_trade(strategy_execution_id, order_id, exchange, symbol, side, size, open_time)

    def log_open_trade(self, strategy_execution_id, order_id, exchange, symbol, side, size, open_time=datetime.now()):
        try:
            with self.conn:
                self.conn.execute('''INSERT INTO trade_log (strategy_execution_id, order_id, exchange, symbol, side, size, open_close, open_time)
                                  VALUES (?, ?, ?, ?, ?, ?, 'Open', ?);''', (strategy_execution_id, order_id, exchange, symbol, side, size, open_time))
                logger.info(f"TradeLogger - Logged open trade for strategy_execution_id: {strategy_execution_id} on exchange: {exchange}")
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error logging open trade for strategy_execution_id: {strategy_execution_id}, exchange: {exchange}. Error: {e}")

    def log_close_trade(self, strategy_execution_id, order_id, pnl, position_delta, close_reason, close_time=datetime.now()):
        try:
            with self.conn:
                self.conn.execute('''UPDATE trade_log 
                                    SET close_time = ?, pnl = ?, position_delta = ?, close_reason = ?, open_close = 'Close' 
                                    WHERE strategy_execution_id = ? AND order_id = ?;''', 
                                (close_time, pnl, position_delta, close_reason, strategy_execution_id, order_id))
                logger.info(f"TradeLogger - Logged close trade for strategy_execution_id: {strategy_execution_id}, order_id: {order_id}")
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error logging close trade for strategy_execution_id: {strategy_execution_id}, order_id: {order_id}, Error: {e}")


    def get_trade_pair_by_execution_id(self, strategy_execution_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trade_log WHERE strategy_execution_id = ?;''', (strategy_execution_id,))
            trades = cursor.fetchall()
            logger.info(f"TradeLogger - Retrieved trades for execution id: {strategy_execution_id}")
            return trades
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error retrieving trades for execution id: {strategy_execution_id}, Error: {e}")
            return []

    def clear_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS trade_log")
            conn.commit()
            self.create_or_access_database()
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error clearing the database: {e}")

import sqlite3
from datetime import datetime
from GlobalUtils.logger import logger

class TradeLogger:
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        try:
            self.conn = self.create_or_access_database()
        except Exception as e:
            logger.error(f"TradeLogger - Error accessing the database: {e}")
            raise e

    def create_or_access_database(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY,
                        strategy_execution_id TEXT NOT NULL,
                        orderId TEXT NOT NULL,
                        exchange TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        size REAL NOT NULL,
                        open_close TEXT NOT NULL,
                        open_time DATETIME,
                        close_time DATETIME,
                        pnl REAL,
                        position_delta REAL,
                        close_reason TEXT
                    );''')
            logger.info("TradeLogger - Database successfully accessed and table created if not exists.")
            return conn
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error creating/accessing the database: {e}")
            raise e

    def log_open_trade(self, strategy_execution_id, orderId, exchange, symbol, side, size, open_time=datetime.now()):
        try:
            with self.conn:
                self.conn.execute('''INSERT INTO trades (strategy_execution_id, orderId, exchange, symbol, side, size, open_close, open_time)
                                  VALUES (?, ?, ?, ?, ?, ?, 'Open', ?);''', (strategy_execution_id, orderId, exchange, symbol, side, size, open_time))
                logger.info(f"TradeLogger - Logged open trade for orderId: {orderId}")
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error logging open trade for orderId: {orderId}, Error: {e}")

    def log_close_trade(self, strategy_execution_id, orderId, pnl, position_delta, close_reason, close_time=datetime.now()):
        try:
            with self.conn:
                self.conn.execute('''UPDATE trades 
                                     SET close_time = ?, pnl = ?, position_delta = ?, close_reason = ?, open_close = 'Close' 
                                     WHERE strategy_execution_id = ? AND orderId = ?;''', 
                                  (close_time, pnl, position_delta, close_reason, strategy_execution_id, orderId))
                logger.info(f"TradeLogger - Logged close trade for orderId: {orderId}")
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error logging close trade for orderId: {orderId}, Error: {e}")

    def get_trade_pair_by_execution_id(self, strategy_execution_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT * FROM trades WHERE strategy_execution_id = ?;''', (strategy_execution_id,))
            trades = cursor.fetchall()
            logger.info(f"TradeLogger - Retrieved trades for execution id: {strategy_execution_id}")
            return trades
        except sqlite3.Error as e:
            logger.error(f"TradeLogger - Error retrieving trades for execution id: {strategy_execution_id}, Error: {e}")
            return []


logger = TradeLogger()
strategy_execution_id = "execution_123"
logger.log_open_trade(strategy_execution_id, '123', 'Binance', 'BTCUSDT', 'Buy', 1.5)
logger.log_open_trade(strategy_execution_id, '456', 'Synthetix', 'BTCUSDT', 'Sell', 1.5)

logger.log_close_trade(strategy_execution_id, '123', 100, 0, 'Take Profit')
logger.log_close_trade(strategy_execution_id, '456', -100, 0, 'Take Profit')

trade_pair = logger.get_trade_pair_by_execution_id(strategy_execution_id)
for trade in trade_pair:
    print(trade)



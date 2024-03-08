import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from TxExecution.Binance.BinancePositionController import BinancePositionController
from TxExecution.ByBit.ByBitPositionController import ByBitPositionController
from TxExecution.Synthetix.SynthetixPositionController import SynthetixPositionController
from TxExecution.Master.MasterPositionControllerUtils import *
from pubsub import pub
from GlobalUtils.logger import logger

class MasterPositionController:
    def __init__(self):
        self.synthetix = SynthetixPositionController()
        self.binance = BinancePositionController()
        self.bybit = ByBitPositionController()
        pub.subscribe(self.execute_trades, 'opportunity_found')

    def execute_trades(self, opportunity):
        try:
            if self.is_already_position_open():
                logger.info("MasterPositionController - Position already open, skipping opportunity.")
                return

            trade_size = self.get_trade_size(opportunity)
            long_exchange, short_exchange = opportunity['long_exchange'], opportunity['short_exchange']
            is_long_binance: bool = long_exchange == 'Binance'
            is_long_synthetix: bool = long_exchange == 'Synthetix'
            is_long_bybit: bool = long_exchange == 'ByBit'

            if 'Binance' in [long_exchange, short_exchange]:
                self.binance.execute_trade(opportunity, is_long=is_long_binance, trade_size=trade_size)

            if 'Synthetix' in [long_exchange, short_exchange]:
                self.synthetix.execute_trade(opportunity, is_long=is_long_synthetix, trade_size=trade_size)
            
            if 'ByBit' in [long_exchange, short_exchange]:
                self.bybit.execute_trade(opportunity, is_long=is_long_bybit, trade_size=trade_size)

            logger.info("MasterPositionController - Trades executed successfully for opportunity.")
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to execute trades for opportunity. Error: {e}")


    def get_trade_size(self, opportunity) -> float:
        try:
            collateral_amounts = self.get_available_collateral_by_exchange()
            trade_size = adjust_collateral_allocation(
                collateral_amounts,
                opportunity['long_exchange'],
                opportunity['short_exchange'])
            
            logger.info(f"MasterPositionController - Trade size calculated: {trade_size}")
            return trade_size
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to calculate trade size for opportunity. Error: {e}")
            return 0.0


    def get_available_collateral_by_exchange(self):
        try:
            synthetix_collateral = self.synthetix.get_available_collateral()
            binance_collateral = self.binance.get_available_collateral()
            bybit_collateral = self.bybit.get_available_collateral()
            
            collateral = {
                "Synthetix": synthetix_collateral,
                "Binance": binance_collateral,
                "Bybit": bybit_collateral
            }
            logger.info("MasterPositionController - Successfully retrieved available collateral from all exchanges.")
            return collateral
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to get available collateral by exchange. Error: {e}")
            return None

    def is_already_position_open(self) -> bool:
        if self.synthetix.is_already_position_open() or self.binance.is_already_position_open() or self.bybit.is_already_position_open():
            logger.info("MasterPositionController - Posotion already open")
            return True
        return False



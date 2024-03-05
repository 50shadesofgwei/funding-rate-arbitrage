from TxExecution.Binance.BinancePositionController import BinancePositionController
from TxExecution.ByBit.ByBitPositionController import ByBitPositionController
from TxExecution.Synthetix.SynthetixPositionController import SynthetixPositionController
from MasterPositionControllerUtils import *
from pubsub import pub

class MasterPositionController:
    def __init__(self):
        self.synthetix = SynthetixPositionController()
        self.binance = BinancePositionController()
        self.bybit = ByBitPositionController()
        pub.subscribe('opportunity_found', )

    def execute_trades(self, opportunity):
        if not self.is_already_position_open():
            return

    def get_trade_size(self, opportunity) -> float:
        collateral_amounts = self.get_available_collateral_by_exchange()
        trade_size = adjust_collateral_allocation(
            collateral_amounts,
            opportunity['long_exchange'],
            opportunity['short_exchange'])
        
        return trade_size

    def get_available_collateral_by_exchange(self):
        synthetix_collateral = self.synthetix.get_available_collateral()
        binance_collateral = self.binance.get_available_collateral()
        bybit_collateral = self.bybit.get_available_collateral()
        
        return {
            "Synthetix": synthetix_collateral,
            "Binance": binance_collateral,
            "Bybit": bybit_collateral
        }

    def is_already_position_open(self) -> bool:
        if self.synthetix.is_already_position_open() or self.binance.is_already_position_open() or self.bybit.is_already_position_open():
            return True
        return False



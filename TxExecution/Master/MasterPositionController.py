from TxExecution.Binance.BinancePositionController import BinancePositionController
from TxExecution.ByBit.ByBitPositionController import ByBitPositionController
from TxExecution.Synthetix.SynthetixPositionController import SynthetixPositionController
from pubsub import pub

class MasterPositionController:
    def __init__(self):
        self.synthetix = SynthetixPositionController()
        self.binance = BinancePositionController()
        self.bybit = ByBitPositionController()
        pub.subscribe()



    def get_trade_size(self, opportunity):
        collateral_amounts = self.get_available_collateral_by_exchange()
        


    def get_available_collateral_by_exchange(self):
        synthetix_collateral = self.synthetix.get_available_collateral()
        binance_collateral = self.binance.get_available_collateral()
        bybit_collateral = self.bybit.get_available_collateral()
        
        return {
            "Synthetix": synthetix_collateral,
            "Binance": binance_collateral,
            "Bybit": bybit_collateral
        }


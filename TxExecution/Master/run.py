from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason
from GlobalUtils.marketDirectory import MarketDirectory

def run():
    exchanges = ['Synthetix', 'Binance']
    MarketDirectory.initialize()
    x = MasterPositionController()
    x.close_position_pair(symbol='ETH', reason=PositionCloseReason.TEST.value, exchanges=exchanges)
    # x = MasterPositionController()
    # x.close_all_positions(PositionCloseReason.TEST.value)

def close_position_pair():
    exchanges = ['Synthetix', 'Binance']
    MarketDirectory.initialize()
    x = MasterPositionController()
    x.close_position_pair(symbol='ETH', reason=PositionCloseReason.TEST.value, exchanges=exchanges)

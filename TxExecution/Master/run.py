from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason

def run():
    x = MasterPositionController()
    x.close_all_positions(PositionCloseReason.TEST.value)

def close_position_pair():
    exchanges = ['Synthetix', 'Binance']
    x = MasterPositionController()
    x.close_position_pair(symbol='ETH', reason=PositionCloseReason.TEST.value, exchanges=exchanges)

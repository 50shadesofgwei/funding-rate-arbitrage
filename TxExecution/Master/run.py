from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason
from GlobalUtils.marketDirectory import MarketDirectory

def run():
    MarketDirectory.initialize()
    x = MasterPositionController()
    exchanges = ['HMX', 'Synthetix']
    x.close_position_pair(symbol='BTC', reason=PositionCloseReason.TEST.value, exchanges=exchanges)


def close_position_pair():
    MarketDirectory.initialize()
    x = MasterPositionController()
    exchanges = ['HMX', 'Synthetix']
    x.close_position_pair(symbol='BTC', reason=PositionCloseReason.TEST.value, exchanges=exchanges)

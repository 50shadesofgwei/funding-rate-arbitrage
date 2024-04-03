from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason

def run():
    x = MasterPositionController()
    x.close_all_positions(PositionCloseReason.TEST.value)

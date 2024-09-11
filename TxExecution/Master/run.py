from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason
# from GlobalUtils.MarketDirectories.SynthetixMarketDirectory import SynthetixMarketDirectory
from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory
from PositionMonitor.TradeDatabase.TradeDatabase import TradeLogger
import argparse

def run(args):
    # SynthetixMarketDirectory.initialize()
    GMXMarketDirectory.initialize()
    x = MasterPositionController()
    y = TradeLogger()
    exchanges = ['GMX', 'ByBit']
    x.close_position_pair(symbol=args.symbol, reason=PositionCloseReason.TEST.value, exchanges=exchanges)

def main():
    parser = argparse.ArgumentParser(description="Close a pair of trades for given asset across HMX and Synthetix")
    parser.add_argument('symbol', type=str, help='The name of the token to close trades for, e.g. BTC or ETH')
    args = parser.parse_args()
    run(args)

def is_position_open():
    x = MasterPositionController()
    # SynthetixMarketDirectory.initialize()
    x.is_already_position_open()


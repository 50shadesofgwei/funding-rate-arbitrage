from Backtesting.Binance.binanceBacktester import BinanceBacktester
from Backtesting.utils.backtestingUtils import *

class MasterBacktester:
    def __init__(self):
        self.binance = BinanceBacktester()
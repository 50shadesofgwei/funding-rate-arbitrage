from Backtesting.Binance.binanceBacktester import BinanceBacktester
from Backtesting.Synthetix.SynthetixBacktester import SynthetixBacktester
from Backtesting.utils.backtestingUtils import *
import json

class MasterBacktester:
    def __init__(self):
        self.binance = BinanceBacktester()
        self.synthetix = SynthetixBacktester()

    def build_data_object(self, symbol: str) -> dict:
        synthetix = self.synthetix.build_statistics_dict(symbol)
        binance = self.binance.build_statistics_dict(symbol)

        data = {
            'synthetix': synthetix,
            'binance': binance
        }

        return data

x = MasterBacktester()
y = x.build_data_object("ETH")

filename = 'event_logs.json'
with open(filename, 'w') as file:
    json.dump(y, file, indent=4)
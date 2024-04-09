from Backtesting.utils.backtestingUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import *
from APICaller.Synthetix.SynthetixCaller import SynthetixCaller
from web3 import *
import os

class SynthetixBacktester:
    def __init__(self):
        self.caller = SynthetixCaller()
        self.contract = get_perps_contract()

    def get_historical_funding_rates(self, symbol: str):
        self.contract.events

    def get_open_interest(self, symbol: str):
        response = self.caller.client.perps.get_market_summary(market_name=symbol)
        data = {
            'symbol': symbol,
            'size': response['size'],
            'max_open_interest': response['max_open_interest'],
            'skew': response['skew'],

        }

    def _get_long_short_ratio(self, market_summary) -> float:
        size = float(market_summary['size'])
        skew = float(market_summary['skew'])
        half_size = size / 2
        half_size_with_skew = half_size + skew
        long_short_ratio = round(half_size_with_skew / half_size, 3)

        return long_short_ratio
        

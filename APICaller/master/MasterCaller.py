import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

import json

from APICaller.Synthetix.SynthetixCaller import SynthetixCaller
from APICaller.Binance.binanceCaller import BinanceCaller
from APICaller.ByBit.ByBitCaller import ByBitCaller
from APICaller.master.MasterUtils import get_all_target_token_lists, get_target_exchanges

class MasterCaller:
    def __init__(self):
        self.synthetix = SynthetixCaller()
        self.binance = BinanceCaller()
        self.bybit = ByBitCaller()
        self.target_token_list_by_exchange = get_all_target_token_lists()
        self.target_exchanges = get_target_exchanges()
        self.filtered_exchange_objects_and_tokens = self.filter_exchanges_and_tokens()

    def filter_exchanges_and_tokens(self):
        all_exchanges = {
            "Synthetix": (self.synthetix, self.target_token_list_by_exchange[0]),
            "Binance": (self.binance, self.target_token_list_by_exchange[1]),
            "ByBit": (self.bybit, self.target_token_list_by_exchange[2]),
        }

        filtered_exchanges = {}
        for exchange_name in self.target_exchanges:
            if exchange_name in all_exchanges:
                filtered_exchanges[exchange_name] = all_exchanges[exchange_name]

        return filtered_exchanges
        
    def get_funding_rates(self) -> list:
        funding_rates = []

        for exchange_name, (exchange, tokens) in self.filtered_exchange_objects_and_tokens.items():
            funding_rates.extend(exchange.get_funding_rates(tokens))

        return funding_rates

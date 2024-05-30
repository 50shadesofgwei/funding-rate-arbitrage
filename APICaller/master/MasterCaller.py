from APICaller.Synthetix.SynthetixCaller import SynthetixCaller
from APICaller.Binance.binanceCaller import BinanceCaller
from APICaller.ByBit.ByBitCaller import ByBitCaller
from APICaller.HMX.HMXCaller import HMXCaller
from APICaller.master.MasterUtils import get_all_target_token_lists, get_target_exchanges
from GlobalUtils.logger import *
import json

class MasterCaller:
    def __init__(self):
        self.synthetix = SynthetixCaller()
        self.binance = BinanceCaller()
        self.bybit = ByBitCaller()
        self.hmx = HMXCaller()
        self.target_token_list_by_exchange = get_all_target_token_lists()
        self.target_exchanges = get_target_exchanges()
        self.filtered_exchange_objects_and_tokens = self.filter_exchanges_and_tokens()

    def filter_exchanges_and_tokens(self):
        try:
            all_exchanges = {
                "Synthetix": (self.synthetix, self.target_token_list_by_exchange[0]),
                "Binance": (self.binance, self.target_token_list_by_exchange[1]),
                "ByBit": (self.bybit, self.target_token_list_by_exchange[2]),
                "HMX": (self.hmx, self.target_token_list_by_exchange[3])
            }

            logger.info(f'MasterAPICaller - Debugging: all_exchanges list = {all_exchanges}')

            filtered_exchanges = {}
            for exchange_name in self.target_exchanges:
                if exchange_name in all_exchanges:
                    filtered_exchanges[exchange_name] = all_exchanges[exchange_name]

            logger.info(f'MasterAPICaller - Debugging: all_exchanges list = {filtered_exchanges}')
            return filtered_exchanges
        except Exception as e:
            logger.error(f"MasterAPICaller - Error filtering exchanges and tokens: {e}")
            return {}
  
    def get_funding_rates(self) -> list:
        try:
            funding_rates = []

            for exchange_name, (exchange, tokens) in self.filtered_exchange_objects_and_tokens.items():
                try:
                    rates = exchange.get_funding_rates(tokens)
                    if rates:
                        funding_rates.extend(rates)
                except Exception as inner_e:
                    logger.error(f"MasterAPICaller - Error getting funding rates from {exchange_name}: {inner_e}")

            return funding_rates
        except Exception as e:
            logger.error(f"MasterAPICaller - Error aggregating funding rates across exchanges: {e}")
            return []
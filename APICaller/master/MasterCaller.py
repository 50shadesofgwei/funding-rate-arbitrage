from APICaller.Synthetix.SynthetixCaller import SynthetixCaller
from APICaller.ByBit.ByBitCaller import ByBitCaller
from APICaller.master.MasterUtils import get_all_target_token_lists, get_target_exchanges
from GlobalUtils.logger import *

class MasterCaller:
    # Initialization based on get_target_exchanges -> Work on this in new branch
    def __init__(self):
        self.synthetix = SynthetixCaller()
        self.bybit = ByBitCaller()
        self.target_token_list_by_exchange = get_all_target_token_lists()
        self.target_exchanges = get_target_exchanges()
        self.filtered_exchange_objects_and_tokens = self.filter_exchanges_and_tokens()

    def filter_exchanges_and_tokens(self):
        try:
            """Creates None if not commented out"""
            all_exchanges = {
                "Synthetix": (self.synthetix, self.target_token_list_by_exchange[0]),
                # "Binance": (self.binance, self.target_token_list_by_exchange[1]),
                "ByBit": (self.bybit, self.target_token_list_by_exchange[2]),
                # "HMX": (self.hmx, self.target_token_list_by_exchange[3]),
                # "GMX": (self.gmx, self.target_token_list_by_exchange[4]),
                # "OKX": (self.okx, self.target_token_list_by_exchange[5])
            }

            filtered_exchanges = {}
            for exchange_name in self.target_exchanges:
                if exchange_name in all_exchanges:
                    filtered_exchanges[exchange_name] = all_exchanges[exchange_name]

            return filtered_exchanges
        except Exception as e:
            logger.error(f"MasterAPICaller - Error filtering exchanges and tokens: {e}")
            return {}
  
    def get_funding_rates(self) -> list:
        funding_rates = []
        if not self.filtered_exchange_objects_and_tokens:
            logger.error("MasterAPICaller - No exchanges and tokens available for fetching funding rates.")
            return funding_rates

        for exchange_name, (exchange, tokens) in self.filtered_exchange_objects_and_tokens.items():
            if not tokens:
                logger.warning(f"MasterAPICaller - No tokens available for {exchange_name}. Skipping.")
                continue

            try:
                rates = exchange.get_funding_rates(tokens)
                if rates:
                    funding_rates.extend(rates)
                else:
                    logger.warning(f"MasterAPICaller - No funding rates returned from {exchange_name}.")
            except Exception as e:
                logger.error(f"MasterAPICaller - Error getting funding rates from {exchange_name}: {e}")

        if not funding_rates:
            logger.error("MasterAPICaller - No funding rates obtained from any exchanges.")
            return None

        return funding_rates

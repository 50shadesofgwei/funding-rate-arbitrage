from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
import time
import sys
import os
from numerize import numerize
from gmx_python_sdk.scripts.v2.get.get_available_liquidity import (
    GetAvailableLiquidity
)
from gmx_python_sdk.scripts.v2.get.get_borrow_apr import GetBorrowAPR
from gmx_python_sdk.scripts.v2.get.get_funding_apr import GetFundingFee
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from GlobalUtils.logger import logger

from gmx_python_sdk.scripts.v2.get.get_available_liquidity import (
    GetAvailableLiquidity
)
from gmx_python_sdk.scripts.v2.get.get_borrow_apr import GetBorrowAPR
from gmx_python_sdk.scripts.v2.get.get_claimable_fees import GetClaimableFees
from gmx_python_sdk.scripts.v2.get.get_contract_balance import (
    GetPoolTVL as ContractTVL
)
from gmx_python_sdk.scripts.v2.get.get_funding_apr import GetFundingFee
from gmx_python_sdk.scripts.v2.get.get_gm_prices import GMPrices
from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from gmx_python_sdk.scripts.v2.get.get_oracle_prices import OraclePrices
from gmx_python_sdk.scripts.v2.get.get_pool_tvl import GetPoolTVL

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

def set_paths():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, '../')
    sys.path.append(target_dir)

set_paths()


ARBITRUM_CONFIG_OBJECT = ConfigManager(chain='arbitrum')
ARBITRUM_CONFIG_OBJECT.set_config(filepath='/Users/jfeasby/SynthetixFundingRateArbitrage/config.yaml')

class GetGMXv2Stats:

    def __init__(self, config, to_json, to_csv):
        self.config = config
        self.to_json = to_json
        self.to_csv = to_csv

    def get_available_liquidity(self):

        return GetAvailableLiquidity(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_borrow_apr(self):

        return GetBorrowAPR(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_claimable_fees(self):

        return GetClaimableFees(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_contract_tvl(self):

        return ContractTVL(
            self.config
        ).get_pool_balances(
            to_json=self.to_json
        )

    def get_funding_apr(self):

        return GetFundingFee(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_gm_price(self):

        return GMPrices(
            self.config
        ).get_price_traders(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_available_markets(self):

        return Markets(
            self.config
        ).get_available_markets()

    def get_open_interest(self):

        return OpenInterest(
            self.config
        ).get_data(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

    def get_oracle_prices(self):

        return OraclePrices(
            self.config.chain
        ).get_recent_prices()

    def get_pool_tvl(self):

        return GetPoolTVL(
            self.config
        ).get_pool_balances(
            to_csv=self.to_csv,
            to_json=self.to_json
        )

def build_stats_class(chain: str) -> GetGMXv2Stats:
    try:
        to_json = True
        to_csv = True

        config = ConfigManager(chain=chain)
        config.set_config(filepath='/Users/jfeasby/SynthetixFundingRateArbitrage/config.yaml')

        stats_class = GetGMXv2Stats(
            config=config,
            to_json=to_json,
            to_csv=to_csv
        )
        return stats_class
    
    except Exception as e:
        logger.error(f'GMXCallerUtils - Failed to build GetGMXStats object. Error: {e}')
        return None

def sort_nested_dict(nested_dict: dict):
    try:
        sorted_keys = sorted(nested_dict.keys(), key=lambda k: nested_dict[k]['net_rate'], reverse=True)
        return sorted_keys
    
    except Exception as e:
        logger.error(f'GMXCallerUtils - Failed to sort nested dictionary by net rate. Error: {e}')
        return None
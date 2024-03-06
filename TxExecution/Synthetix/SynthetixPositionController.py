import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
from GlobalUtils.globalUtils import *
import json

class SynthetixPositionController:
    def __init__(self):
        self.client = get_synthetix_client()

    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        full_asset_name = get_full_asset_name(opportunity['symbol'])
        trade_size_in_asset = get_asset_amount_for_given_dollar_amount(full_asset_name, trade_size)
        adjusted_trade_size = adjust_trade_size_for_direction(trade_size_in_asset, is_long)

        self.client.perps.commit_order(adjusted_trade_size, market_name=opportunity['symbol'], submit=True)


    def get_available_collateral(self) -> float:
        account = self.get_default_account()
        balances = self.client.perps.get_collateral_balances(account)
        susd_balance = balances["sUSD"]

        return susd_balance

    def get_default_account(self):
        default_account = self.check_for_accounts()
        default_account = default_account[0]

        return default_account

    def check_for_accounts(self):
        account_ids = self.client.perps.account_ids
        if not account_ids:
            self.create_account()
        else:
            return account_ids 

    def create_account(self):
        self.client.perps.create_account(submit=True)

    def is_already_position_open(self) -> bool:
        positions = self.client.perps.get_open_positions()
        if not positions: 
            return False
        for key, position in positions.items():
            if float(position['position_size']) != 0:
                return True
        return False


test = SynthetixPositionController()
ids = test.check_for_accounts()
print(ids)

import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
import json

class SynthetixPositionController:
    def __init__(self):
        self.client = get_synthetix_client()

    def check_for_accounts(self):
        account_ids = self.client.perps.account_ids
        if not account_ids:
            self.create_account()
        else:
            return account_ids 

    def create_account(self):
        self.client.perps.create_account(submit=True)

    def is_already_position_open(self) -> bool:
        positions = self.client.futures_position_information()
        for position in positions:
            if float(position['positionAmt']) != 0:
                return True
        return False

test = SynthetixPositionController()
test.check_for_accounts()

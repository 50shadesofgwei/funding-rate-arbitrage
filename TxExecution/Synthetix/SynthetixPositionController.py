import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
import time

class SynthetixPositionController:
    def __init__(self):
        self.client = get_synthetix_client()
        self.leverage_factor = float(os.getenv('TRADE_LEVERAGE'))

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        try:
            if not self.is_already_position_open():
                adjusted_trade_size = self.calculate_adjusted_trade_size(opportunity, is_long, trade_size)
                self.client.perps.commit_order(adjusted_trade_size, market_name=opportunity['symbol'], submit=True)
                time.sleep(3)

                if self.is_already_position_open():
                    logger.info("Synthetix - Order executed successfully")
            else:
                logger.error("Synthetix - SynthetixPositionController.execute_trade called while position already open")
        except Exception as e:
            logger.info(f"Synthetix - An error occurred while executing a trade: {e}")

    def close_position(self, market_id: int):
        try:
            position = self.client.perps.get_open_position(market_id=market_id)
            if position and position['position_size'] != 0:
                size = position['position_size']
                inverse_size = size * -1
                self.client.perps.commit_order(size=inverse_size, market_id=market_id, submit=True)
                time.sleep(3)
                
                
                if not self.is_already_position_open():
                    logger.info('Synthetix - Position successfully closed.')
                else:
                    logger.error('Synthetix - Failed to close position. Please check manually.')
            else:
                logger.error("Synthetix - No open position to close.")
        except Exception as e:
            logger.error(f"Synthetix - An error occurred while trying to close a position: {e}")

    def add_collateral(self, market_id: int, amount: float):
        try:
            self.client.perps.modify_collateral(
                amount=amount, 
                market_id=market_id, 
                submit=True
            )
            logger.info(f"Synthetix - Successfully added {amount} collateral to market ID {market_id}.")
        except Exception as e:
            logger.error(f"Synthetix - An error occurred while attempting to add collateral: {e}")


    def create_account(self):
        try:
            account = self.client.perps.create_account(submit=True)
            logger.info(f"Synthetix - Account creation successful: {account}")
        except Exception as e:
            logger.error(f"Synthetix - Account creation failed. Error: {e}")


    def collateral_approval(self, token_address: str, amount: int):
        try:
            perps_address = self.client.spot.market_proxy.address
            approve_tx = self.client.approve(
                token_address=token_address, 
                target_address=perps_address, 
                amount=amount,
                submit=True
            )
            logger.info(f"Synthetix - Collateral approval transaction successful. Transaction ID: {approve_tx}")
        except Exception as e:
            logger.error(f"Synthetix - Collateral approval failed for token {token_address} with amount {amount}. Error: {e}")

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_available_collateral(self):
        try:
            account = self.get_default_account()
            balances = self.client.perps.get_collateral_balances(account)
            logger.info(f"Synthetix - Collateral balances called successfully: {balances}")
            return balances
        except Exception as e:
            logger.error(f"Synthetix - Failed to get available collateral. Error: {e}")
            return None

    def get_default_account(self):
        try:
            default_account = self.check_for_accounts()
            if default_account:
                default_account = default_account[0]
                logger.info("Synthetix - Successfully retrieved default account.")
                return default_account
            else:
                logger.error("Synthetix - No accounts found.")
                return None
        except Exception as e:
            logger.error(f"Synthetix - Failed to get the default account. Error: {e}")
            return None


    def check_for_accounts(self):
        try:
            account_ids = self.client.perps.account_ids
            if not account_ids:
                logger.info("Synthetix - No accounts found for wallet, creating new one.")
                self.create_account()
                return self.client.perps.account_ids
            else:
                logger.info("Synthetix - Accounts checked and found successfully.")
                return account_ids
        except Exception as e:
            logger.error(f"Synthetix - Error checking for or creating accounts: {e}")
            return None
 

    def calculate_adjusted_trade_size(self, opportunity, is_long: bool, trade_size: float) -> float:
        try:
            full_asset_name = get_full_asset_name(opportunity['symbol'])
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(full_asset_name, trade_size)
            trade_size_with_leverage = trade_size_in_asset * self.leverage_factor
            adjusted_trade_size = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            return adjusted_trade_size
        except Exception as e:
            logger.error(f"Synthetix - Failed to calculate adjusted trade size. Error: {e}")
            raise


    def is_already_position_open(self) -> bool:
        try:
            positions = self.client.perps.get_open_positions()
            if not positions: 
                return False
            for key, position in positions.items():
                if float(position['position_size']) != 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking if position is open: {e}")
            return False


test = SynthetixPositionController()
x = test.is_already_position_open()
print(x)


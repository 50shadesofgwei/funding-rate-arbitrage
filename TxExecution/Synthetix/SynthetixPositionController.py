from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
from APICaller.master.MasterUtils import get_target_tokens_for_synthetix
from TxExecution.Synthetix.SynthetixPositionControllerUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import *
from GlobalUtils.marketDirectory import MarketDirectory
import time
import math
from GlobalUtils.globalUtils import GLOBAL_SYNTHETIX_CLIENT

class SynthetixPositionController:
    def __init__(self):
        self.client = GLOBAL_SYNTHETIX_CLIENT
        self.leverage_factor = float(os.getenv('TRADE_LEVERAGE'))

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trade(self, opportunity: dict, is_long: bool, trade_size: float):
        try:
            if not self.is_already_position_open():
                account_id: int = self.get_default_account()
                adjusted_trade_size: float = self.calculate_adjusted_trade_size(opportunity, is_long, trade_size)
                market_name = str(opportunity['symbol'])

                response = self.client.perps.commit_order(
                    size=adjusted_trade_size, 
                    market_name=market_name, 
                    account_id=account_id, 
                    submit=True
                )
                
                if is_transaction_hash(response):
                    time.sleep(15)
                    position_data = self.handle_position_opened(market_name)
                    return position_data
                else:
                    logger.error(f"SynthetixPositionController - Failed to execute order for {market_name}")
                    return None
            else:
                logger.error("SynthetixPositionController - execute_trade called while position already open")
                return None

        except Exception as e:
            logger.error(f"SynthetixPositionController - An error occurred while executing a trade for {market_name}: {e}", exc_info=True)
            return None


    def close_all_positions(self):
        close_results = []
        selected_markets = get_target_tokens_for_synthetix()
        try:
            for market in selected_markets:
                try:
                    reason = PositionCloseReason.CLOSE_ALL_POSITIONS.value
                    close_details = self.close_position(symbol=market, reason=reason)
                    if close_details:
                        close_results.append(close_details)
                except Exception as e:
                    logger.error(f"SynthetixPositionController - Error closing position for market {market}: {e}")
        except Exception as e:
            logger.error(f"SynthetixPositionController - General error in close all positions: {e}")
        
        return close_results if close_results else None


    def close_position(self, symbol: str, reason: str) -> dict:
        max_retries = 2 
        retry_delay_in_seconds = 3 
        market_id = MarketDirectory.get_market_id(symbol) 
        
        for attempt in range(max_retries):
            try:
                position = self.client.perps.get_open_position(market_id=market_id)
                if position and position['position_size'] != 0:
                    close_position_details = {
                        'symbol': symbol,
                        'exchange': 'Synthetix',
                        'pnl': position['pnl'],
                        'accrued_funding': position['accrued_funding'],
                        'reason': reason
                    }

                    size = position['position_size']
                    inverse_size = size * -1
                    response = self.client.perps.commit_order(size=inverse_size, market_id=market_id, submit=True)

                    if is_transaction_hash(response):
                        self.handle_position_closed(position_report=close_position_details)
                        logger.info(f'SynthetixPositionController - Position successfully closed: {close_position_details}')
                        return close_position_details
                    else:
                        logger.error('SynthetixPositionController - Failed to close position. Please check manually.')
                        return None

            except Exception as e:
                logger.error(f"SynthetixPositionController - An error occurred while trying to close a position: {e}")
                if attempt < max_retries - 1:
                    logger.info("SynthetixPositionController - Attempting to retry closing position after delay...")
                    time.sleep(retry_delay_in_seconds)
                else:
                    return None

    def approve_and_deposit_collateral(self, token_address: str, amount: int):
        try:
            market_id = self.client.spot.markets_by_name[f"sUSDC"]["market_id"]
            wrapped_token = self.client.spot.markets_by_id[market_id]["contract"]
            self._approve_spot_market_to_spend_collateral(token_address, amount)
            time.sleep(1)
            self._wrap_collateral(amount)
            time.sleep(1)
            self._approve_spot_market_to_spend_collateral(wrapped_token.address, amount)
            time.sleep(1)
            self._execute_atomic_order(amount, 'sell')
            time.sleep(1)
            self._approve_collateral_for_perps_market_proxy(amount)
            time.sleep(1)
            self._add_collateral(amount)
            time.sleep(1)

        except Exception as e:
            logger.error(f"SynthetixPositionController - An error occurred while attempting to add collateral: {e}")
            return None

    def _add_collateral(self, amount: int):
        try:
            account_id = self.get_default_account()
            tx = self.client.perps.modify_collateral(
                amount=amount, 
                market_name="sUSD", 
                account_id=account_id,
                submit=True
            )
            if is_transaction_hash(tx):
                logger.info(f"SynthetixPositionController - Successfully added {amount} to collateral, market_name = sUSD.")
        except Exception as e:
            logger.error(f"SynthetixPositionController - An error occurred while attempting to add collateral: {e}")

    def _create_account(self):
        try:
            account = self.client.perps.create_account(submit=True)
            logger.info(f"SynthetixPositionController - Account creation successful: {account}")
        except Exception as e:
            logger.error(f"SynthetixPositionController - Account creation failed. Error: {e}")

    def _approve_collateral_for_spot_market_proxy(self, amount: int):
        try:
            market_id = self.client.spot.markets_by_name[f"sUSDC"]["market_id"]
            amount=amount*10**18
            spot_market_proxy_address = self.client.spot.market_proxy.address
            approve_tx = self.client.spot.approve(
                target_address=spot_market_proxy_address, 
                market_id=market_id,
                amount=amount,
                submit=True
            )
            if is_transaction_hash(approve_tx):
                logger.info(f"SynthetixPositionController - Spot market collateral approval transaction successful. Transaction ID: {approve_tx}")
        except Exception as e:
            logger.error(f"SynthetixPositionController - Collateral approval for spot market failed. Error: {e}")

    def _approve_spot_market_to_spend_collateral(self, token_address: str, amount: int):
        try:
            spot_market_proxy_address = self.client.spot.market_proxy.address
            approve_tx = self.client.approve(
                token_address, 
                spot_market_proxy_address,
                amount,
                submit=True
            )
            if is_transaction_hash(approve_tx):
                logger.info(f"SynthetixPositionController - Approved spot market collateral to spend collateral transaction successful. Transaction ID: {approve_tx}")
        except Exception as e:
            logger.error(f"SynthetixPositionController - Spot market spending collateral approval for token: {token_address}, amount: {amount} failed. Error: {e}")
            return None


    def _approve_collateral_for_perps_market_proxy(self, amount: int):
        try:
            amount=amount*10**18
            perps_market_proxy_address: str = self.client.perps.market_proxy.address
            approve_tx = self.client.spot.approve(
                target_address=perps_market_proxy_address, 
                market_name="sUSD",
                amount=amount,
                submit=True
            )
            if is_transaction_hash(approve_tx):
                logger.info(f"SynthetixPositionController - Perps market collateral approval transaction successful. Transaction ID: {approve_tx}")
        except Exception as e:
            logger.error(f"SynthetixPositionController - Collateral approval for perps market failed. Error: {e}")

    def _wrap_collateral(self, amount: int):
        try:
            market_id = self.client.spot.markets_by_name[f"sUSDC"]["market_id"]
            wrap_tx = self.client.spot.wrap(amount, market_id, submit=True)
            if is_transaction_hash(wrap_tx):
                logger.info(f"SynthetixPositionController - Wrap tx executed successfully: {wrap_tx}")

        except Exception as e:
            logger.error(f"SynthetixPositionController - Failed to wrap USDC <> sUSDC. amount = {amount}. Error: {e}")

    def _execute_atomic_order(self, amount: int, side: str):
        order_tx = self.client.spot.atomic_order(side, amount, market_name="sUSDC", submit=True)
        if is_transaction_hash(order_tx):
            logger.info(f"SynthetixPositionController - Atomic order transaction successful. Side: {side}, Transaction ID: {order_tx}")



    ######################
    ### READ FUNCTIONS ###
    ######################

    def handle_position_opened(self, market_name: str):
        try:
            position = self.client.perps.get_open_position(market_name=market_name)
            position['symbol'] = market_name
            margin_details = self.client.perps.get_margin_info()
            position_details = {
                'position': position,
                'margin_details': margin_details
            }
            trade_data = parse_trade_data_from_position_details(position_details)
            return trade_data
        except Exception as e:
            logger.error(f"SynthetixPositionController - Failed to retrieve position data upon opening. Error: {e}")
            return None

    def handle_position_closed(self, position_report: dict):
        try:
            pub.sendMessage(EventsDirectory.POSITION_CLOSED.value, position_report=position_report)
            return 
        except Exception as e:
            logger.error(f"SynthetixPositionController - Failed to retrieve handle position closing. Error: {e}")
            return None

    def get_available_collateral(self) -> float:
        try:
            account = self.get_default_account()
            balances = self.client.perps.get_collateral_balances(account)
            collateral = balances['sUSD']
            logger.info(f"SynthetixPositionController - Collateral balance called successfully: {collateral}")
            return collateral
        except Exception as e:
            logger.error(f"SynthetixPositionController - Failed to get available collateral. Error: {e}")
            return None

    def get_default_account(self):
        try:
            default_account = self.check_for_accounts()
            if default_account:
                default_account = default_account[0]
                return default_account
            else:
                logger.error("SynthetixPositionController - No accounts found.")
                return None
        except Exception as e:
            logger.error(f"SynthetixPositionController - Failed to get the default account. Error: {e}")
            return None

    def check_for_accounts(self):
        try:
            account_ids = self.client.perps.account_ids
            if not account_ids:
                logger.info("SynthetixPositionController - No accounts found for wallet, creating new one.")
                self._create_account()
                return self.client.perps.account_ids
            else:
                return account_ids
        except Exception as e:
            logger.error(f"SynthetixPositionController - Error checking for or creating accounts: {e}")
            return None
 
    def calculate_adjusted_trade_size(self, opportunity: dict, is_long: bool, trade_size: float) -> float:
        try:
            symbol = opportunity['symbol']
            trade_size_with_leverage = trade_size * self.leverage_factor
            trade_size_in_asset_with_leverage = get_asset_amount_for_given_dollar_amount(symbol, trade_size_with_leverage)
            adjusted_trade_size_raw = adjust_trade_size_for_direction(trade_size_in_asset_with_leverage, is_long)
            adjusted_trade_size = round(adjusted_trade_size_raw, 3)

            return adjusted_trade_size
        except Exception as e:
            logger.error(f"SynthetixPositionController - Failed to calculate adjusted trade size for {symbol}. Error: {e}",
                        exc_info=True) 
            return None


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
            logger.error(f"SynthetixPositionController - Error while checking if position is open: {e}")
            return False

    def calculate_premium(self, symbol: str, size: float) -> float:
        max_retries = 5
        retries = 0
        
        market_id = MarketDirectory.get_market_id(symbol)
        
        while retries < max_retries:
            try:
                quote_dict = self.client.perps.get_quote(size=size, market_id=market_id)
                
                if quote_dict is None:
                    time.sleep(0.23)
                    retries += 1
                    logger.warning(f"SynthetixPositionController - Null quote received, retrying {retries}/{max_retries} for symbol {symbol} with market ID {market_id}")
                    continue
                
                index_price = float(quote_dict['index_price'])
                fill_price = float(quote_dict['fill_price'])
                
                if fill_price == 0:
                    logger.error(f"SynthetixPositionController - Zero fill price error for symbol {symbol} with market ID {market_id}")
                    return None
                
                premium = (fill_price - index_price) / index_price
                return premium
            
            except Exception as e:
                logger.error(f"SynthetixPositionController - Error calculating premium for symbol {symbol}: {e}")
                return None
        
        logger.error(f"SynthetixPositionController - Failed to get a valid quote after {max_retries} retries for symbol {symbol} with market ID {market_id}")
        return None


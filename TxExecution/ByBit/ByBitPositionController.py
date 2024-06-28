from pybit.unified_trading import HTTP
from APICaller.ByBit.ByBitUtils import *
from pubsub import pub
import os
import json
from dotenv import load_dotenv
import requests
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from APICaller.master.MasterUtils import TARGET_TOKENS
from TxExecution.ByBit.ByBitPositionControllerUtils import *

load_dotenv()

class ByBitPositionController:
    
    def __init__(self):
        self.client = get_ByBit_client()
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.leverage = os.getenv('TRADE_LEVERAGE')
        # self.set_leverage_for_all_assets(TARGET_TOKENS)

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        try:
            symbol = opportunity['symbol']
            side = get_side(is_long)
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, trade_size)
            self.client.place_order(
                category="linear",
                symbol=symbol+'USDT',
                side=side,
                orderType="Market",
                qty=trade_size_in_asset,
            )
            logger.info(f"ByBitPositionController - Trade executed: symbol={symbol} side={'Long' if is_long else 'Short'}, Size={trade_size_in_asset}")
        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to execute trade for {symbol}. Error: {e}")
            return None

    def close_all_positions(self):
        try:
            self.client.cancel_all_orders(category='linear')
            logger.info("ByBitPositionController - All positions closed successfully.")
        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to close all positions. Error: {e}")

    def close_position_for_symbol(self, symbol: str):
        try:
            response = self.client.get_positions(
                category="linear",
                symbol=symbol
            )
            close_order_details = parse_close_order_data_from_position_response(response)
            
            close_position_response = self.client.place_order(
                category="linear",
                symbol=symbol,
                side=close_order_details['side'],
                orderType="Market",
                qty=close_order_details['size']
            )

            order_id: str = close_position_response['result']['orderId']

            time.sleep(2)
            if self._was_trade_executed_successfully(order_id):
                logger.info(f'ByBitPositionController - Order closed successfully for symbol {symbol}, orderId: {order_id}')
                return None

        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to close position for symbol {symbol}. Error: {e}")
            return None
            
    def set_leverage_for_all_assets(self, tokens):
        for token in tokens:
            try:
                if token["is_target"]:
                    symbol = token["token"] + "USDT"
                    current_leverage = self.get_leverage_factor_for_token(symbol)
                    if not is_leverage_already_correct(current_leverage, self.leverage):
                        self.client.set_leverage(
                            category="linear",
                            symbol=symbol,
                            buyLeverage=self.leverage,
                            sellLeverage=self.leverage
                        )
                        logger.info(f"ByBitPositionController - Leverage set for {symbol}: {self.leverage}x")
            except Exception as e:
                logger.error(f"ByBitPositionController - Failed to set leverage for {symbol}. Error: {e}")


    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_leverage_factor_for_token(self, symbol: str) -> float:
        try:
            response = self.client.get_positions(category='linear', symbol=symbol)
            if response['retCode'] == 0 and response['result']['list']:
                leverage_factor = response['result']['list'][0]['leverage']
                return float(leverage_factor)
            else:
                logger.error(f"ByBitPositionController - Could not find leverage factor for symbol {symbol}.")
                return 0.0
        except Exception as e:
            logger.error(f"ByBitPositionController - Error retrieving leverage factor for {symbol}. Error: {e}")
            return 0.0


    def get_available_collateral(self) -> float:
        try:
            usdt_collateral = self.client.get_coin_balance(accountType="UNIFIED", coin="USDT")
            if usdt_collateral and usdt_collateral["result"] and usdt_collateral["result"]["balance"]:
                collateral_amount = float(usdt_collateral["result"]["balance"]["walletBalance"])
                return collateral_amount
            else:
                logger.error("ByBitPositionController - Failed to retrieve USDT collateral balance. Result structure was unexpected.")
                return 0.0
        except Exception as e:
            logger.error(f"ByBitPositionController - Error retrieving available USDT collateral. Error: {e}")
            return 0.0

    def is_already_position_open(self) -> bool:
        try:
            url = "https://api.bybit.com/private/linear/position/list"
            headers = {
                "X-Api-Key": self.api_key,
                "X-Api-Secret": self.api_secret
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                positions = response.json().get('result', [])
                for position in positions:
                    if position.get('size', 0) > 0:
                        return True
                return False
            else:
                logger.error(f"ByBitPositionController - Failed to get open positions. HTTP status code: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"ByBitPositionController - Error checking if position is open. Error: {e}")
            return False

    def _was_trade_executed_successfully(self, order_id: str) -> bool:
        attempt = 0
        retries: int = 3

        while attempt < retries:
            try:
                response = self.client.get_order_history(
                    category="linear",
                    orderId=order_id
                )

                if response and response.get('retCode') == 0 and 'result' in response and 'list' in response['result']:
                    list = response['result']['list']
                    order_status = list[0]['orderStatus']
                    if order_status == 'Filled':
                        return True
                    else:
                        return False

            except Exception as e:
                logger.error(f"ByBitPositionController - Attempt {attempt + 1} failed to check if trade was executed successfully. Error: {e}")
            
            attempt += 1

        logger.error(f"ByBitPositionController - All {retries} attempts failed to check if trade was executed successfully for order_id: {order_id}")
        return None



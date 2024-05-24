from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from APICaller.Binance.binanceUtils import BinanceEnvVars
from APICaller.master.MasterUtils import get_target_tokens_for_binance
from binance.um_futures import UMFutures as Client
from binance.enums import *
from TxExecution.Binance.BinancePositionControllerUtils import *
import os
import time
import pubsub
from dotenv import load_dotenv

load_dotenv()

class BinancePositionController:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(key=api_key, secret=api_secret, base_url="https://testnet.binancefuture.com")
        self.leverage = int(os.getenv('TRADE_LEVERAGE'))
        # self.set_leverage_for_all_assets(TARGET_TOKENS)

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trade(self, opportunity, is_long: bool, trade_size: float) -> dict:
        order_with_amount = {} 
        try:

            order = get_order_from_opportunity(opportunity, is_long)
            amount = calculate_adjusted_trade_size(opportunity, is_long, trade_size, self.leverage)
            order_with_amount = add_amount_to_order(order, amount)

            response = self.client.new_order(
                symbol=order_with_amount['symbol'],
                side=order_with_amount['side'],
                type=order_with_amount['type'],
                quantity=order_with_amount['quantity'])

            if not is_expected_api_response_format_for_new_order(response):
                return None

            time.sleep(2)
            if self.is_order_filled(order_id=int(response['orderId']), symbol=response['symbol']):
                logger.info(f"BinancePositionController - Trade executed: {order_with_amount['symbol']} {order_with_amount['side']}, Quantity: {order_with_amount['quantity']}, Order id: {response['orderId']}")
                try:
                    position_object = self.get_position_object_from_response(response)
                    return position_object
                except Exception as e:
                    logger.error(f"BinancePositionController - Failed to obtain liquidation price for {response['symbol']}. Error: {e}")
                    return response 
            else:
                logger.info("BinancePositionController - Order not filled.")
                return None
        except Exception as e:
            logger.error(f"BinancePositionController - Error encountered while placing trade for {order_with_amount.get('symbol', 'unknown')}. Error: {e}")
            return None

    @log_function_call
    def close_all_positions(self):
        selected_markets = get_target_tokens_for_binance()
        positions = []
        for market in selected_markets:
            close_details = self.close_position(market, reason="TEST")
            positions.append(close_details)
        
        return positions[0]

    def close_position(self, symbol: str, reason: str):
        try:
            position_info = self.client.get_position_risk(symbol=symbol)
            
            if not position_info or 'positionAmt' not in position_info[0]:
                logger.error(f"BinancePositionController - No open position found for {symbol}, or missing required fields.")
                return
            
            position_amount = float(position_info[0]['positionAmt'])
            is_long = is_long_trade(position_amount)

            if position_amount == 0:
                logger.info(f"BinancePositionController - No open position to close for {symbol}.")
                return

            close_side = "BUY" if is_long == False else "SELL"
            close_quantity_raw = abs(position_amount)
            close_quantity = round(close_quantity_raw, 4)

            response = self.client.new_order(
                symbol=symbol, 
                side=close_side,
                type=ORDER_TYPE_MARKET,
                quantity=close_quantity)

            time.sleep(3)
            if self.is_order_filled(response['orderId'], symbol):
                close_position_details = self.parse_close_position_details_from_api_response(position_info, reason, symbol)
                self.handle_position_closed(close_position_details)
                logger.info(f"BinancePositionController - Open position for symbol {symbol} has been successfully closed: {close_position_details}")
            else:
                logger.error(f"BinancePositionController - Failed to close the open position for symbol {symbol}. Error: {e}")

        except Exception as e:
            logger.error(f"BinancePositionController - Failed to close position for symbol {symbol}. Error: {e}")


    def set_leverage_for_all_assets(self, tokens):
        try:
            for token in tokens:
                if token["is_target"]:
                    symbol = token["token"] + "USDT"
                    x = self.client.change_leverage(
                        symbol=symbol,
                        leverage=self.leverage,
                    )
                    logger.info(f"BinancePositionController - Leverage for {symbol} set to {self.leverage}.")
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to set leverage for assets. Error: {e}")

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_position_object_from_response(self, response) -> dict:
        try:
            symbol = response['symbol']
            order_id = response['orderId']
            side = get_side(response['side'])
            size = float(response['origQty'])
            liquidation_price = self.get_liquidation_price(response['symbol'])

            return {
                'exchange': 'Binance',
                'symbol': symbol,
                'side': side,
                'size': size,
                'order_id': order_id,
                'liquidation_price': liquidation_price
            }
        
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to generate position object for {response['symbol']}. Error: {e}")
            return None

    def is_already_position_open(self) -> bool:
        try:
            selected_markets = get_target_tokens_for_binance()
            for token in selected_markets:
                orders = self.client.get_position_risk(symbol=token)
                if float(orders[0]['positionAmt']) > 0:
                    logger.info(f"BinancePositionController - Open position found for {token}")
                    return True
            
            return False

        except Exception as e:
            logger.error(f"BinancePositionController - Error while checking if position is open for target tokens. Error: {e}")
            return False

    def is_order_filled(self, order_id: int, symbol: str) -> bool:
        try:
            order_status = self.client.query_order(symbol=symbol, orderId=order_id)
            if order_status['status'] == 'FILLED':
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"BinancePositionController - is_filled check for order {order_id} for symbol {symbol} failed. Error: {e}")
            return False

    def get_liquidation_price(self, symbol: str) -> float:
        try:
            response = self.client.get_position_risk(symbol=symbol)
            
            if isinstance(response, list) and len(response) > 0:
                position_risk = response[0]
            
                if 'liquidationPrice' in position_risk:
                    return float(position_risk['liquidationPrice'])
                else:
                    logger.error(f"BinancePositionController - No liquidationPrice found in position risk response for {symbol}.")
                    return None 
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to get liquidation price for position. Asset: {symbol}, Error: {e}")
            return None 

    def get_available_collateral(self) -> float:
        try:
            account_details = self.client.balance()
            for asset_detail in account_details:
                if asset_detail['asset'] == 'USDT':
                    return float(asset_detail['balance'])

        except Exception as e:
            logger.error(f"BinancePositionController - Failed to get available collateral. Error: {e}")
            return 0.0

    def handle_position_opened(self, response: dict):
        try:
            position_object = self.get_position_object_from_response(response)
            return position_object
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to handle position opening for {response['symbol']}. Error: {e}")
            return None

    @log_function_call
    def handle_position_closed(self, close_position_details: dict):
        try:
            logger.error(f'DEBUGGING: BPC handle_position_closed arg = {close_position_details}')
            pub.sendMessage(topicName=EventsDirectory.POSITION_CLOSED.value, position_report=close_position_details)
            return 
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to handle position closed with details: {close_position_details}. Error: {e}")
            return None 
    
    def parse_close_position_details_from_api_response(self, APIresponse: dict, reason: str, symbol: str) -> dict:
        close_position_details = {
                        'symbol': symbol,
                        'exchange': 'Binance',
                        'pnl': float(APIresponse[0]['unRealizedProfit']),
                        'accrued_funding': 0.0,
                        'reason': reason
                    }
        return close_position_details

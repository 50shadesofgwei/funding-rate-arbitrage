from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from APICaller.Binance.binanceUtils import BinanceEnvVars
from APICaller.master.MasterUtils import TARGET_TOKENS
from binance.um_futures import UMFutures as Client
from binance.enums import *
from TxExecution.Binance.BinancePositionControllerUtils import *
import os
import time
from dotenv import load_dotenv

load_dotenv()

class BinancePositionController:
    @log_function_call
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(key=api_key, secret=api_secret, base_url="https://testnet.binancefuture.com")
        self.leverage = int(os.getenv('TRADE_LEVERAGE'))
        self.set_leverage_for_all_assets(TARGET_TOKENS)

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    @log_function_call
    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        order_with_amount = {} 
        try:

            order = get_order_from_opportunity(opportunity, is_long)
            amount = calculate_adjusted_trade_size(opportunity, is_long, trade_size)
            order_with_amount = add_amount_to_order(order, amount)

            response = self.client.new_order(
                symbol=order_with_amount['symbol'],
                side=order_with_amount['side'],
                type=order_with_amount['type'],
                quantity=order_with_amount['quantity'])
            
            logger.info(f"BinancePositionController - placing order w/ amount: {order_with_amount['quantity']}")

            if not isinstance(response, dict) or 'orderId' not in response or 'symbol' not in response:
                logger.error("BinancePositionController - Invalid response structure from new_order.")
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
            logger.error(f"BinancePositionController - Failed to format database object for {order_with_amount.get('symbol', 'unknown')}. Error: {e}")
            return None

    def close_all_positions(self):
        positions = []
        for market in ALL_MARKETS:
            close_details = self.close_position(market)
            positions.append(close_details)
        
        return positions[0]

    def close_position(self, symbol: str):
        try:
            # Fetch the current open position for the symbol
            position_info = self.client.get_position_risk(symbol=symbol)
            
            if not position_info or 'positionAmt' not in position_info[0]:
                logger.error(f"BinancePositionController - No open position found for {symbol}, or missing required fields.")
                return
            
            position_amount = float(position_info[0]['positionAmt'])
            if position_amount > 0:
                is_long = True
            elif position_amount < 0:
                is_long = False
        

            if position_amount == 0:
                logger.info(f"BinancePositionController - No open position to close for {symbol}.")
                return

            close_side = "BUY" if is_long == False else "SELL"
            close_quantity_raw = abs(position_amount)
            close_quantity = round(close_quantity_raw, 4)

            x = self.client.new_order(
                symbol=symbol, 
                side=close_side,
                type=ORDER_TYPE_MARKET,
                quantity=close_quantity)

            time.sleep(3)
            if self.is_order_filled(x['orderId'], symbol):
                close_position_details = {
                    'exchange': 'Binance',
                    'pnl': float(position_info[0]['unRealizedProfit']),
                    'accrued_fees': 0.0
                }
                logger.info(f"BinancePositionController - Open position for symbol {symbol} has been successfully closed: {close_position_details}")
                return close_position_details
            else:
                logger.error(f"BinancePositionController - Failed to close the open position for symbol {symbol}.")

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

    def is_already_position_open(self) -> bool:
        try:
            for token in TARGET_TOKENS:
                symbol = token["token"] + "USDT"
                orders = self.client.get_position_risk(symbol=symbol)
            if float(orders[0]['positionAmt']) > 0:
                logger.error(f"BinancePositionController - Open position found for {symbol}")
                return True
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
        response = self.client.get_position_risk(symbol=symbol)
        
        if isinstance(response, list) and len(response) > 0:
            position_risk = response[0]
            logger.info(f"BinancePositionController - position_risk object = {position_risk}")
            
            if 'liquidationPrice' in position_risk:
                return float(position_risk['liquidationPrice'])
            else:
                logger.error(f"BinancePositionController - No liquidationPrice found in position risk for {symbol}.")
                return 0.0 
        else:
            logger.error(f"BinancePositionController - Unexpected response structure or empty response for position risk of {symbol}.")
            return 0.0 


    def get_available_collateral(self) -> float:
        try:
            account_details = self.client.balance()
            for asset_detail in account_details:
                if asset_detail['asset'] == 'USDT':
                    return float(asset_detail['balance'])
            logger.info("BinancePositionController - USDT collateral not found, returning 0.0")
            return 0.0
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to get available collateral. Error: {e}")
            return 0.0
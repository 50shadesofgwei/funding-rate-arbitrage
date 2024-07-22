from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from APICaller.master.MasterUtils import get_target_tokens_for_okx
from TxExecution.OKX.OKXPositionControllerUtils import *
import os
import time
import pubsub
from dotenv import load_dotenv

load_dotenv()

class OKXPositionController:
    def __init__(self):
        self.account_client = GLOBAL_OKX_ACCOUNT_CLIENT
        self.trade_client = GLOBAL_OKX_TRADE_CLIENT
        self.leverage = int(os.getenv('TRADE_LEVERAGE'))
        self.set_leverage_for_all_assets([])# if empty, then use get_target_tokens_for_okx

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def get_tick_lot_size(self, symbol:str):
        try:
            response = self.account_client.get_instruments(instType="SWAP")
            tgt_inst = None
            for inst in response['data']:
                if inst['instId'] == symbol:
                    tgt_inst = inst

            return float(tgt_inst['tickSz'])
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to obtain tick size for {response['symbol']}. Error: {e}")
            return None

    def get_contract_value(self, symbol:str):
        try:
            response = self.account_client.get_instruments(instType="SWAP")
            tgt_inst = None
            for inst in response['data']:
                if inst['instId'] == symbol:
                    tgt_inst = inst

            return float(tgt_inst['ctVal'])
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to obtain tick size for {response['symbol']}. Error: {e}")
            return None

    def execute_trade(self, opportunity, is_long: bool, trade_size: float) -> dict:
        order_with_amount = {}

        try:

            order = get_order_from_opportunity(opportunity, is_long)
            symbol = order['symbol']

            amount = calculate_adjusted_trade_size(opportunity, is_long, trade_size, self.leverage)
            contract_value = self.get_contract_value(symbol=symbol)
            amount = amount / contract_value

            order_with_amount = add_amount_to_order(order, amount)

            response = self.trade_client.place_order(
                instId = symbol,
                tdMode = 'isolated',
                side   = order_with_amount['side'],
                posSide= order_with_amount['posSide'],
                ordType= 'market',
                sz     = order_with_amount['quantity']
            )

            if not is_expected_api_response_format_for_new_order(response):
                return None

            time.sleep(2)

            orderId = response['data'][0]['ordId']
            # response does not has enough info
            passing_response = {
                'symbol' : symbol,
                'orderId' : orderId,
                'side' : order_with_amount['side'],
                'origQty' : order_with_amount['quantity']
            }

            if self.is_order_filled(order_id=int(orderId), symbol=symbol):
                logger.info(f"OKXPositionController - Trade executed: {order_with_amount['symbol']} {order_with_amount['side']}, Quantity: {order_with_amount['quantity']}, Order id: {orderId}")
                try:
                    position_object = self.get_position_object_from_response(passing_response)
                    return position_object
                except Exception as e:
                    logger.error(f"PositionController - Failed to obtain liquidation price for {response['symbol']}. Error: {e}")
                    return response 
            else:
                logger.info("OKXPositionController - Order not filled.")
                return None
        except Exception as e:
            logger.error(f"OKXPositionController - Error encountered while placing trade for {order_with_amount.get('symbol', 'unknown')}. Error: {e}")
            return None

    def close_all_positions(self):
        selected_markets = get_target_tokens_for_okx()
        positions = []
        for market in selected_markets:
            close_details = self.close_position(market, reason="TEST")
            positions.append(close_details)
        
        return positions[0]

    def close_position(self, symbol: str, reason: str):
        try:
            positions = self.account_client.get_positions() # TODO, move to close all positions
            if(len(positions['data']) == 0):
                logger.error(f"OKXPositionController - No open position found for {symbol}, or missing required fields.")
                return
            position_info = None
            for pos in positions['data']:
                if pos['instId'] == symbol:
                    position_info = pos

            if position_info == None:
                logger.error(f"OKXPositionController - No open position found for {symbol}, or missing required fields.")
                return
            
            position_amount = float(position_info['availPos'])
            is_long = position_info['posSide'] == 'long'

            if position_amount == 0:
                logger.info(f"OKXPositionController - No open position to close for {symbol}.")
                return

            close_side = "buy" if is_long == False else "sell"
            close_quantity_raw = abs(position_amount)
            close_quantity = round(close_quantity_raw, 4)

            response = self.trade_client.place_order(
                instId = symbol,
                tdMode = 'isolated',
                side   = close_side,
                posSide= 'long' if is_long else 'short',
                ordType= 'market',
                sz     = close_quantity
            )

            orderId = response['data'][0]['ordId']
            time.sleep(3)
            if self.is_order_filled(orderId, symbol):
                close_position_details = self.parse_close_position_details_from_api_response(position_info, reason, symbol)
                self.handle_position_closed(close_position_details)
                logger.info(f"OKXPositionController - Open position for symbol {symbol} has been successfully closed: {close_position_details}")
            else:
                logger.error(f"OKXPositionController - Failed to close the open position for symbol {symbol}. Error: Close Order is not filled ")

        except Exception as e:
            logger.error(f"OKXPositionController - Failed to close position for symbol {symbol}. Error: {e}")


    def set_leverage_for_all_assets(self, tokens):

        try:
            if(len(tokens) == 0):
                tokens = get_target_tokens_for_okx()

            for token in tokens:
                if token["is_target"]:
                    symbol = token["token"] + "-USDT-SWAP"

                    result = self.account_client.set_leverage(
                        instId=symbol,
                        lever=str(self.leverage),
                        mgnMode="isolated",      # currently isolated margin mode
                        posSide="long"
                    )
                    result = self.account_client.set_leverage(
                        instId=symbol,
                        lever=str(self.leverage),
                        mgnMode="isolated",      # currently isolated margin mode
                        posSide="short"
                    )

                    logger.info(f"OKXPositionController - Leverage for {symbol} set to {self.leverage}.")
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to set leverage for assets. Error: {e}")

    # Set leverage to be 5x for all isolated-margin BTC-USDT SWAP positions,
    # by providing any SWAP instId with BTC-USDT as the underlying
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
                'exchange': 'OKX',
                'symbol': symbol,
                'side': side,
                'size': size,   # size in contract unit
                'order_id': order_id,
                'liquidation_price': liquidation_price
            }
        
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to generate position object for {response['symbol']}. Error: {e}")
            return None

    def is_already_position_open(self) -> bool:
        # TODO: log all open positions or only log the first one?
        try:
            selected_markets = get_target_tokens_for_okx()
            response = self.account_client.get_positions()
            positions = response['data']
            holding_tokens = [x['instId'] for x in positions if float(x['availPos']) > 0]

            for token in selected_markets:
                if token in holding_tokens:
                    logger.info(f"OKXPositionController - Open position found for {token}")
                    return True
            return False

        except Exception as e:
            logger.error(f"OKXPositionController - Error while checking if position is open for target tokens. Error: {e}")
            return False

    def is_order_filled(self, order_id: int, symbol: str) -> bool:
        try:
            order_status = self.trade_client.get_order(instId=symbol,
                                                       ordId=order_id)

            is_filled = order_status['data'][0]['sz'] == order_status['data'][0]['accFillSz']
            if is_filled:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"OKXPositionController - is_filled check for order {order_id} for symbol {symbol} failed. Error: {e}")
            return False

    def get_liquidation_price(self, symbol: str) -> float:
        try:
            response = self.account_client.get_positions()
            if len(response['data']) > 0:
                for position_risk in response['data']:
                    if position_risk['instId'] == symbol:
                        return float(position_risk['liqPx'])
                else:
                    logger.error(f"OKXPositionController - No liquidationPrice found in position risk response for {symbol}.")
                    return None 
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to get liquidation price for position. Asset: {symbol}, Error: {e}")
            return None 

    def get_available_collateral(self) -> float:
        try:
            account_details = self.client.get_account_balance(ccy = 'USDT')
            return float(account_details['data'][0]['details'][0]['eqUsd'])

        except Exception as e:
            logger.error(f"OKXPositionController - Failed to get available collateral. Error: {e}")
            return 0.0

    def handle_position_opened(self, response: dict):
        try:
            position_object = self.get_position_object_from_response(response)
            return position_object
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to handle position opening for {response['symbol']}. Error: {e}")
            return None

    def handle_position_closed(self, close_position_details: dict):
        try:
            logger.error(f'DEBUGGING: BPC handle_position_closed arg = {close_position_details}')
            pub.sendMessage(topicName=EventsDirectory.POSITION_CLOSED.value, position_report=close_position_details)
            return 
        except Exception as e:
            logger.error(f"OKXPositionController - Failed to handle position closed with details: {close_position_details}. Error: {e}")
            return None 
    
    def parse_close_position_details_from_api_response(self, APIresponse: dict, reason: str, symbol: str) -> dict:
        close_position_details = {
                        'symbol': symbol,
                        'exchange': 'OKX',
                        'pnl': float(APIresponse['realizedPnl']),   #TODO, currently, leverage asset raw pnl, not related to long and short
                        'accrued_funding': 0.0,
                        'reason': reason
                    }
        return close_position_details

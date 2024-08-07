from APICaller.ByBit.ByBitUtils import *
from pubsub import pub
import os
from dotenv import load_dotenv
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from TxExecution.ByBit.ByBitPositionControllerUtils import *
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason


load_dotenv()

class ByBitPositionController:
    
    def __init__(self):
        self.client = GLOBAL_BYBIT_CLIENT
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.leverage = float(os.getenv('TRADE_LEVERAGE'))
        # self.set_leverage_for_all_assets(TARGET_TOKENS)

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        try:
            symbol = opportunity['symbol']
            side = get_side(is_long)
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, trade_size)
            trade_size_with_leverage = trade_size_in_asset * self.leverage
            full_symbol = symbol+'USDT'
            qty_step_raw = self.get_qty_step(full_symbol)
            qty_step = normalize_qty_step(qty_step_raw)
            truncated_value = str(f"{trade_size_with_leverage:.{qty_step}f}")

            response = self.client.place_order(
                category="linear",
                symbol=full_symbol,
                side=side,
                orderType="Market",
                qty=truncated_value,
            )

            order_id = response['result']['orderId']

            time.sleep(2)
            if self._was_trade_executed_successfully(order_id):
                logger.info(f"ByBitPositionController - Trade executed: symbol={symbol} side={'Long' if is_long else 'Short'}, Size={truncated_value}")
                try:
                    position_object = self.get_position_object(
                    opportunity,
                    response,
                    is_long,
                    truncated_value
                    )
                    return position_object
                except Exception as ie:
                    logger.error(f"ByBitPositionController - Failed to build position object, despite trade executing successfully for symbol {symbol}. Error: {ie}")
                    return response 
            else:
                logger.info("BinancePositionController - Order not filled after 2 seconds.")
                return None
        
        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to execute trade for {symbol}. Error: {e}", exc_info=True)
            return None

    def close_all_positions(self):
        try:
            self.client.cancel_all_orders(category='linear')
            logger.info("ByBitPositionController - All positions closed successfully.")
        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to close all positions. Error: {e}")

    def close_position(self, symbol: str, reason: str = None):
        try:
            response = self.client.get_positions(
                category="linear",
                symbol=symbol+'USDT'
            )
            cum_realized_pnl = float(response['result']['list'][0]['cumRealisedPnl'])
            unrealized_pnl = float(response['result']['list'][0]['unrealisedPnl'])
            total_pnl = cum_realized_pnl + unrealized_pnl

            close_order = parse_close_order_data_from_position_response(response)
            
            close_position_response = self.client.place_order(
                category="linear",
                symbol=symbol+'USDT',
                side=close_order['side'],
                orderType="Market",
                qty=close_order['size']
            )

            order_id: str = close_position_response['result']['orderId']
            close_position_details = build_close_position_details(
                reason,
                symbol,
                total_pnl
            )

            time.sleep(2)
            if self._was_trade_executed_successfully(order_id):
                logger.info(f'ByBitPositionController - Order closed successfully for symbol {symbol}, orderId: {order_id}')
                self.handle_position_closed(close_position_details)
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

    def handle_position_closed(self, close_position_details: dict):
        try:
            pub.sendMessage(topicName=EventsDirectory.POSITION_CLOSED.value, position_report=close_position_details)
            return 
        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to handle position closed with details: {close_position_details}. Error: {e}")
            return None

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

    def is_already_position_open(self):
        try:
            response = self.client.get_positions(
                category="linear",
                settleCoin='USDT'
            )

            positions = response.get('result', {}).get('list', [])
            if positions:
                return True
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
                        continue

            except Exception as e:
                logger.error(f"ByBitPositionController - Attempt {attempt + 1} failed to check if trade was executed successfully. Error: {e}")
            
            time.sleep(1)
            attempt += 1

        logger.error(f"ByBitPositionController - All {retries} attempts failed to check if trade was executed successfully for order_id: {order_id}")
        return None

    def get_position_object(self, opportunity: dict, response: dict, is_long: bool, truncated_value: str) -> dict:
        try:
            symbol = opportunity['symbol']
            result = response['result']
            order_id = result.get('orderId', None)
            side = 'Long' if is_long else 'Short'
            size = float(truncated_value)
            liquidation_price = self.get_liquidation_price(symbol)

            return {
                'exchange': 'ByBit',
                'symbol': symbol,
                'side': side,
                'size': size,
                'order_id': order_id,
                'liquidation_price': liquidation_price
            }
        
        except Exception as e:
            logger.error(f"ByBitPositionController - Failed to generate position object for {symbol}. Error: {e}")
            return None
    
    def get_liquidation_price(self, symbol: str) -> float:
        try:
            response = self.client.get_positions(
                category='linear',
                symbol=symbol+'USDT')
            positions = response.get('result', {}).get('list', [])
            if not positions:
                return None
            
            liq_price_str = positions[0].get('liqPrice', None)

            if liq_price_str is not None:
                return float(liq_price_str)
            else:
                return None
        except (ValueError, TypeError) as vte:
            logger.error(f'ByBitPositionController - Value or Type error while calling liquidation price for symbol {symbol}. Error: {vte}')
            return None
        except Exception as e:
            logger.error(f'ByBitPositionController - Error while calling liquidation price for symbol {symbol}. Error: {e}')
            return None
    
    def get_qty_step(self, symbol: str) -> float:
        try:
            response = self.client.get_instruments_info(
                category='linear',
                symbol=symbol
            )

            instruments = response.get('result', {}).get('list', [])
            if not instruments:
                return None
            
            qty_step_str = instruments[0].get('lotSizeFilter', {}).get('qtyStep', None)

            if qty_step_str is not None:
                return float(qty_step_str)
            else:
                return None
        except Exception as e:
            logger.error(f'ByBitPositionController - Error while retrieving qtyStep for symbol {symbol}. Error: {e}')
            return None


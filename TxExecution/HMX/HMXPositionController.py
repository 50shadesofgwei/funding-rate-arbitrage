import os
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from HMXPositionControllerUtils import *
from hmx2.constants.tokens import COLLATERAL_USDC
import time
from hexbytes import HexBytes

class HMXPositionController:
    def __init__(self):
        self.client = GLOBAL_HMX_CLIENT
        self.account = str(os.getenv('ADDRESS'))
        self.leverage_factor = float(os.getenv('TRADE_LEVERAGE'))

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trade(self, opportunity: dict, is_long: bool, trade_size: float):
        try:
            if not self.is_already_position_open():
                symbol = opportunity['symbol']
                market = get_market_for_symbol(symbol)
                adjusted_trade_size = self.calculate_adjusted_trade_size(is_long, trade_size)
                response = self.client.private.create_market_order(
                    0,
                    market_index=market,
                    buy=is_long,
                    size=adjusted_trade_size,
                    reduce_only=False,
                    tp_token=COLLATERAL_USDC
                )

                time.sleep(7)
                if not self.is_already_position_open():
                    logger.error(f'HMXPositionController - Failed to open position for symbol {symbol}.')
                    return None


                self.handle_position_opened()

                return response

        except Exception as e:
            logger.error(f'HMXPositionController - Error while opening trade for symbol {symbol}, Error: {e}')
            return None

    def close_position(self, symbol: str, reason: str):
        max_retries = 2 
        retry_delay_in_seconds = 3 
        market_index = get_market_for_symbol(symbol)
        
        for attempt in range(max_retries):
            try:
                position = self.client.public.get_position_info(
                    self.account,
                    0,
                    market_index
                    )

                if position and position['position_size'] != 0:
                    close_position_details = {
                        'symbol': symbol,
                        'exchange': 'HMX',
                        'pnl': position['pnl'],
                        'accrued_funding': position['funding_fee'],
                        'reason': reason
                    }

                    size = float(position['position_size'])
                    inverse_size = size * -1
                    side = is_long(inverse_size)
                    self.client.private.create_market_order(
                        0, 
                        market_index=market_index, 
                        buy=side, 
                        size=inverse_size,
                        reduce_only=False,
                        tp_token=COLLATERAL_USDC
                    )
                    
                    time.sleep(7)
                    if self.is_already_position_open():
                        logger.error(f'HMXPositionController - Failed to close position for symbol {symbol}.')
                        return None

                    self.handle_position_closed(position_report=close_position_details)
                    logger.info(f'HMXPositionController - Position successfully closed: {close_position_details}')
                    return 
                else:
                    logger.error('HMXPositionController - Failed to close position. Please check manually.')
                    raise Exception('HMXPositionController - Commit order failed, no transaction hash returned.')

            except Exception as e:
                logger.error(f"HMXPositionController - An error occurred while trying to close a position: {e}")
                if attempt < max_retries - 1:
                    logger.info("HMXPositionController - Attempting to retry closing position after delay...")
                    time.sleep(retry_delay_in_seconds)
                else:
                    raise e


    def deposit_erc20_collateral(self, token_address: str, amount: float):
        """
        Takes amount in normalized terms - i.e. not token decimals
        eg. 100.00 = 100 USDC
        """
        try:
            response = self.client.private.deposit_erc20_collateral(0, token_address, amount)
            tx_hash = HexBytes.hex(response['tx'])
            time.sleep(3)
            if is_transaction_hash(tx_hash):
                logger.info(f'HMXPositionController - Collateral deposit tx successful. Token Address: {token_address}, Amount = {amount}')
                return

        except Exception as e:
            logger.error(f'HMXPositionController - Failed to deposit collateral. Token Address: {token_address}, Amount: {amount}. Error: {e}')
            return None


    ######################
    ### READ FUNCTIONS ###
    ######################

    def is_already_position_open(self) -> bool:
        try:
            position_list = self.client.public.get_all_position_info(self.account, 0)
            if not position_list:
                return False
            for position in position_list: 
                if float(position['position_size']) != 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"HMXPositionController - Error while checking if position is open: {e}")
            return False

    def calculate_adjusted_trade_size(self, is_long: bool, trade_size: float) -> float:
        try:
            trade_size_with_leverage = trade_size * self.leverage_factor
            adjusted_trade_size_raw = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            adjusted_trade_size = round(adjusted_trade_size_raw, 3)
            return adjusted_trade_size
        except Exception as e:
            logger.error(f"HMXPositionController - Failed to calculate adjusted trade size. Error: {e}")
            return None

    def handle_position_opened(self, symbol: str, response: dict):
        try:
            market_id = get_market_for_symbol(symbol)
            position_response = self.client.public.get_position_info(self.account, 0, market_id)
            avg_entry_price = float(position_response['avg_entry_price'])
            size = get_position_size_from_response(response, avg_entry_price)

            if size > 0:
                side = "LONG"
            elif size < 0:
                side = "SHORT"

            position = self.get_position_object(symbol, side, size)
            return position
        
        except Exception as e:
            logger.error(f'HMXPositionController - Failed to handle position opened. Error: {e}')

    def handle_position_closed(self, position_report: dict):
        try:
            pub.sendMessage(EventsDirectory.POSITION_CLOSED.value, position_report=position_report)
            return 
        except Exception as e:
            logger.error(f"HMXPositionController - Failed to handle position closing. Error: {e}")
            return None

    def get_position_object(self, symbol: str, side: str, size: float, ):
        liquidation_price = self.get_liquidation_price()
        position_object = {
                'exchange': 'HMX',
                'symbol': symbol,
                'side': side,
                'size': size,
                'liquidation_price': liquidation_price
            }

    def get_liquidation_price(self, symbol: str) -> float:
        market_index = get_market_for_symbol(symbol)
        position = self.client.public.get_position_info(
            self.account,
            0,
            market_index,
            )

        size = position['position_size']
        y = self.client.public.__multicall_all_market_data()
        print(y)



test_op = {
    'symbol': 'ETH'
}

x = HMXPositionController()
y = x.get_liquidation_price('ETH')

import os
from GlobalUtils.globalUtils import *
from APICaller.Synthetix.SynthetixUtils import GLOBAL_SYNTHETIX_CLIENT
from APICaller.HMX.HMXCallerUtils import GLOBAL_HMX_CLIENT
from GlobalUtils.logger import logger
from TxExecution.HMX.HMXPositionControllerUtils import *
from APICaller.master.MasterUtils import get_target_tokens_for_HMX
from PositionMonitor.Master.MasterPositionMonitorUtils import PositionCloseReason
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
                symbol = str(opportunity['symbol'])
                side: str = 'Long' if is_long else 'Short'
                market = get_market_for_symbol(symbol)
                adjusted_trade_size_usd = self.calculate_adjusted_trade_size_usd(trade_size)
      
                self.client.private.create_market_order(
                    0,
                    market_index=market,
                    buy=is_long,
                    size=adjusted_trade_size_usd,
                    reduce_only=False,
                    tp_token=COLLATERAL_USDC
                )

                time.sleep(15)
                if not self.is_already_position_open():
                    logger.error(f'HMXPositionController - Failed to open position for symbol {symbol}.')
                    return None

                size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, adjusted_trade_size_usd)
                position_details = self.handle_position_opened(symbol, size_in_asset, side)

                return position_details

        except Exception as e:
            logger.error(f'HMXPositionController - Error while opening trade for symbol {symbol}, Error: {e}')
            return None


    def close_all_positions(self):
        try:
            tokens = get_target_tokens_for_HMX
            for token in tokens:
                self.close_position(token, reason=PositionCloseReason.CLOSE_ALL_POSITIONS.value)
        
        except Exception as e:
            logger.error(f'HMXPositionController - Error while closing all trades. Error: {e}')
            return None

    def close_position(self, symbol: str, reason: str):
        max_retries = 10
        retry_delay_in_seconds = 30
        market_index = get_market_for_symbol(symbol)
        
        for attempt in range(max_retries):
            try:
                position = self.client.public.get_position_info(
                    self.account,
                    0,
                    market_index
                    )

                if position and position['position_size'] != 0:
                    funding_fee = float(position['funding_fee'])
                    pnl = position['pnl']
                    pnl = pnl - funding_fee

                    accrued_funding = funding_fee * -1
                    close_position_details = {
                        'symbol': symbol,
                        'exchange': 'HMX',
                        'pnl': pnl,
                        'accrued_funding': accrued_funding,
                        'reason': reason
                    }

                    size = float(position['position_size'])
                    inverse_size = size * -1
                    side = is_long(inverse_size)
                    abs_size = abs(size)
                    self.client.private.create_market_order(
                        0, 
                        market_index=market_index, 
                        buy=side, 
                        size=abs_size,
                        reduce_only=False,
                        tp_token=COLLATERAL_USDC
                    )
                    
                    time.sleep(15)
                    if self.is_already_position_open():
                        logger.error(f'HMXPositionController - Position on HMX still open 5 mins after attempting to close. Symbol: {symbol}.')
                        return None

                    self.handle_position_closed(position_report=close_position_details)
                    logger.info(f'HMXPositionController - Position successfully closed: {close_position_details}')
                    return 
                else:
                    logger.error('HMXPositionController - Failed to close position. Please check manually.')
                    return None

            except Exception as e:
                logger.error(f"HMXPositionController - An error occurred while trying to close a position: {e}")
                if attempt < max_retries - 1:
                    logger.info("HMXPositionController - Attempting to retry closing position after delay...")
                    time.sleep(retry_delay_in_seconds)
                else:
                    return None


    def deposit_erc20_collateral(self, token_address: str, amount: float):
        """
        Takes amount in normalized terms - i.e. not token decimals
        eg. 100.00 = 100 USDC
        """
        try:
            response = self.client.private.deposit_erc20_collateral(0, token_address, amount)
            tx_hash: HexBytes = HexBytes.hex(response['tx'])
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

    def calculate_adjusted_trade_size_usd(self, trade_size: float) -> float:
        try:
            trade_size_with_leverage = trade_size * self.leverage_factor
            adjusted_trade_size_usd = round(trade_size_with_leverage, 3)

            return adjusted_trade_size_usd
        except Exception as e:
            logger.error(f"HMXPositionController - Failed to calculate adjusted trade size. Error: {e}")
            return None

    def handle_position_opened(self, symbol: str, size_in_asset: float, side: str):
        try:
            position = self.get_position_object(symbol, side, size_in_asset)
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

    def get_position_object(self, symbol: str, side: str, size: float) -> dict:
        try:
            liquidation_price = self.get_liquidation_price(symbol, side)
            position_object = {
                    'exchange': 'HMX',
                    'symbol': symbol,
                    'side': side,
                    'size_in_asset': size,
                    'liquidation_price': liquidation_price
                }
            return position_object

        except Exception as e:
            logger.error(f"HMXPositionController - Failed to get position object for symbol {symbol}. Error: {e}")
            return None

    def get_liquidation_price(self, symbol: str, side: str) -> float:
        try:
            market_index = get_market_for_symbol(symbol)
            if market_index is None:
                logger.error(f"No market index found for symbol: {symbol}")
                return None

            position = self.client.public.get_position_info(self.account, 0, market_index)
            response = self.client.public.get_market_info(market_index)

            pnl = position['pnl']
            asset_price = get_price_from_pyth(symbol, pyth_client=GLOBAL_SYNTHETIX_CLIENT)
            available_collateral = self.get_available_collateral()
            available_collateral = available_collateral + pnl
            margin_details = response['margin']
            is_long = True if side.lower() == 'long' else False

            maintenance_margin_fraction = float(margin_details['maintenance_margin_fraction_bps']) / 10000 
            position_size = abs(float(position['position_size']))
            size_in_asset = get_asset_amount_for_given_dollar_amount(symbol, position_size)
            maintenance_margin_requirement = position_size * maintenance_margin_fraction

            liquidation_params = {
                "size_in_asset": size_in_asset,
                "size_usd": position_size,
                "is_long": is_long,
                "available_margin": available_collateral,
                "asset_price": asset_price,
                "maintenance_margin_requirement": maintenance_margin_requirement,
                "maintenance_margin_fraction": maintenance_margin_fraction
            }

            liquidation_price = calculate_liquidation_price(liquidation_params)
            return liquidation_price

        except KeyError as ke:
            logger.error(f"Key error in get_liquidation_price: {ke}. Missing data for symbol: {symbol}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_liquidation_price for symbol: {symbol}. Error: {e}")
            return None


    def get_available_collateral(self) -> float:
        try:
            available_collateral = self.client.public.get_collateral_usd(self.account, 0)
            return float(available_collateral)

        except Exception as e:
            logger.error(f"HMXPositionController - Failed to get available collateral. Error: {e}")
            return None

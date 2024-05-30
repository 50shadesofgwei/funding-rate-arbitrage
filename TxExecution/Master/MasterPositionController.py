from TxExecution.Binance.BinancePositionController import BinancePositionController
from TxExecution.Synthetix.SynthetixPositionController import SynthetixPositionController
from TxExecution.HMX.HMXPositionController import HMXPositionController
from TxExecution.Master.MasterPositionControllerUtils import *
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from APICaller.master.MasterUtils import get_full_symbol_for_binance
from pubsub import pub
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *

class MasterPositionController:
    def __init__(self):
        self.synthetix = SynthetixPositionController()
        self.binance = BinancePositionController()
        self.hmx = HMXPositionController()

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trades(self, opportunity: dict):
        try:
            if self.is_already_position_open():
                logger.info("MasterPositionController - Position already open, skipping opportunity.")
                return None

            trade_size = self.get_trade_size(opportunity)
            logger.info(f'MasterPositionController:execute_trades - getting trade size for opportunity object: {opportunity}')
            exchanges = {
                'long_exchange': opportunity[0]['long_exchange'],
                'short_exchange': opportunity[0]['short_exchange']
            }
            symbol = opportunity['symbol']

            position_data_dict = {}

            for exchange_name in exchanges:
                execute_trade_method = getattr(self, exchange_name.lower()).execute_trade
                position_data = execute_trade_method(
                    opportunity, 
                    is_long=exchange_name == opportunity['long_exchange'], 
                    trade_size=trade_size
                )

                logger.info(f"MasterPositionController - {exchange_name} trade execution response: {position_data}")

                if position_data:
                    position_data_dict[exchange_name] = position_data

 
            if len(position_data_dict) == 2:
                logger.info(f"Publishing POSITION_OPENED with position_data: {position_data_dict}")
                pub.sendMessage(EventsDirectory.POSITION_OPENED.value, position_data=position_data_dict)
                logger.info("MasterPositionController:execute_trades - Trades executed successfully for opportunity.")
            else:
                self.close_position_pair(symbol=symbol, reason=PositionCloseReason.POSITION_OPEN_ERROR.value, exchanges=exchanges)
                missing_exchanges = set([exchanges[0], exchanges[1]]) - set(position_data_dict.keys())
                logger.error(f"MasterPositionController:execute_trades - Failed to execute trades on all required exchanges. Missing: {missing_exchanges}. Cancelling trades.")

        except Exception as e:
            logger.error(f"MasterPositionController:execute_trades - Failed to process trades for opportunity. Error: {e}")
            self.close_position_pair(symbol=symbol, reason=PositionCloseReason.POSITION_OPEN_ERROR.value, exchanges=exchanges)

    @log_function_call
    def close_all_positions(self, reason: str):
        synthetix_position_report = self.synthetix.close_all_positions()
        binance_position_report = self.binance.close_all_positions()
        position_report = {
            'Synthetix': synthetix_position_report,
            'Binance': binance_position_report,
            'close_reason': reason
        }
        logger.info(f'MasterPositionController - Closing positions with position report: {position_report}')
        pub.sendMessage(EventsDirectory.POSITION_CLOSED.value, position_report=position_report)

    @log_function_call
    def close_position_pair(self, symbol: str, reason: str, exchanges: list):
        try:
            logger.error(f'DEBUGGING: MasterPositionController - Closing position pair with args: symbol={symbol}, reason={reason}, exchanges={exchanges}')
            for exchange_name in exchanges:
                    if exchange_name == 'Binance':
                        symbol = get_full_symbol_for_binance(symbol)
                    close_position_method = getattr(self, exchange_name.lower()).close_position
                    close_position_method(
                        symbol=symbol, 
                        reason=reason
                    )
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to close trade pair for symbol {symbol} and exchange pair {exchanges}. Error: {e}")

    def subscribe_to_events(self):
        pub.subscribe(self.execute_trades, EventsDirectory.OPPORTUNITY_FOUND.value)
        pub.subscribe(self.close_position_pair, EventsDirectory.CLOSE_POSITION_PAIR.value)
        pub.subscribe(self.close_all_positions, EventsDirectory.CLOSE_ALL_POSITIONS.value)

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_trade_size(self, opportunity):
        try:
            print(opportunity)
            # long_exchange = opportunity['long_exchange']
            # short_exchange = opportunity['short_exchange']
            # exchanges = {
            #     'long_exchange': long_exchange,
            #     'short_exchange': short_exchange
            # }

            # logger.info(f'MPC - Debugging - exchanges object = {exchanges}, collateral_amounts = {collateral_amounts}, trade_size = {trade_size}.')

            # collateral_amounts = self.get_available_collateral_for_exchanges(exchanges)

            # trade_size = adjust_collateral_allocation(collateral_amounts, opportunity['long_exchange'], opportunity['short_exchange'])

            
            return 
        except Exception as e:
            logger.error(f"MasterPositionController:get_trade_size - Failed to print opportunity. Error: {e}")
            return None

    def get_available_collateral_for_exchange(self, exchange: str) -> float:
        method_caller = getattr(self, exchange.lower()).get_available_collateral
        collateral = method_caller()
        return collateral



    def get_available_collateral_for_exchanges(self, exchanges: dict):
        try:
            long_exchange = exchanges['long_exchange']
            short_exchange = exchanges['short_exchange']
            long_collateral = self.get_available_collateral_for_exchange(long_exchange)
            short_collateral = self.get_available_collateral_for_exchange(short_exchange)

            collateral = {
                'long_exchange': long_collateral,
                'short_exchange': short_collateral
            }

            logger.info(f'MPC - Debugging: collateral object = {collateral}')

            return collateral
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to get available collateral by exchange. Error: {e}")
            return None

    def is_already_position_open(self) -> bool:
        try:
            is_synthetix_position = False
            is_hmx_position = False
            is_binance_position = False

            try:
                is_synthetix_position = self.synthetix.is_already_position_open()
            except Exception as e:
                logger.error(f'MasterPositionController:is_already_position_open - Error checking Synthetix position: {e}')

            try:
                is_hmx_position = self.hmx.is_already_position_open()
            except Exception as e:
                logger.error(f'MasterPositionController:is_already_position_open - Error checking HMX position: {e}')

            try:
                is_binance_position = self.binance.is_already_position_open()
            except Exception as e:
                logger.error(f'MasterPositionController:is_already_position_open - Error checking Binance position: {e}')

            positions_open = [
                is_synthetix_position,
                is_hmx_position,
                is_binance_position
            ]

            if any(positions_open):
                logger.info(f"MasterPositionController - Position already open: SNX: {is_synthetix_position}, HMX: {is_hmx_position}, Binance: {is_binance_position}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f'MasterPositionController - Unexpected error when checking positions: {e}')
            return False


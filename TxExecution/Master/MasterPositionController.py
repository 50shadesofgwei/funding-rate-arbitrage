from TxExecution.Binance.BinancePositionController import BinancePositionController
from TxExecution.Synthetix.SynthetixPositionController import SynthetixPositionController
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

    #######################
    ### WRITE FUNCTIONS ###
    #######################

    def execute_trades(self, opportunity):
        try:
            if self.is_already_position_open():
                logger.info("MasterPositionController - Position already open, skipping opportunity.")
                return

            trade_size_raw = self.get_trade_size(opportunity)
            trade_size = round(trade_size_raw, 6)
            long_exchange, short_exchange = opportunity['long_exchange'], opportunity['short_exchange']

            position_data_dict = {}

            for exchange_name in [long_exchange, short_exchange]:
                execute_trade_method = getattr(self, exchange_name.lower()).execute_trade
                position_data = execute_trade_method(
                    opportunity, 
                    is_long=exchange_name == long_exchange, 
                    trade_size=trade_size
                )

                logger.info(f"MasterPositionController - {exchange_name} trade execution response: {position_data}")

                if position_data:
                    position_data_dict[exchange_name] = position_data

 
            if len(position_data_dict) == 2:
                logger.info(f"Publishing POSITION_OPENED with position_data: {position_data_dict}")
                pub.sendMessage(EventsDirectory.POSITION_OPENED.value, position_data=position_data_dict)
                logger.info("MasterPositionController - Trades executed successfully for opportunity.")
            else:
                self.close_all_positions(PositionCloseReason.POSITION_OPEN_ERROR.value)
                missing_exchanges = set([long_exchange, short_exchange]) - set(position_data_dict.keys())
                logger.error(f"MasterPositionController - Failed to execute trades on all required exchanges. Missing: {missing_exchanges}. Cancelling trades.")

        except Exception as e:
            logger.error(f"MasterPositionController - Failed to process trades for opportunity. Error: {e}")
            self.close_all_positions(PositionCloseReason.POSITION_OPEN_ERROR.value)

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

    def get_trade_size(self, opportunity) -> float:
        try:
            exchanges = {
                'long_exchange': opportunity['long_exchange'],
                'short_exchange': opportunity['short_exchange']
            }
            collateral_amounts = self.get_available_collateral_for_exchanges(exchanges)
            trade_size = adjust_collateral_allocation(
                collateral_amounts,
                opportunity['long_exchange'],
                opportunity['short_exchange'])
            
            return trade_size
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to calculate trade size for opportunity. Error: {e}")
            return None

    def get_available_collateral_for_exchanges(self, exchanges: dict):
        try:
            long_exchange = exchanges['long_exchange']
            short_exchange = exchanges['short_exchange']
            get_long_available_collateral_method = getattr(self, long_exchange.lower()).get_available_collateral
            long_collateral = get_long_available_collateral_method()
            get_short_available_collateral_method = getattr(self, short_exchange.lower()).get_available_collateral
            short_collateral = get_short_available_collateral_method()

            collateral = {
                long_exchange: long_collateral,
                short_exchange: short_collateral
            }

            return collateral
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to get available collateral by exchange. Error: {e}")
            return None

    def is_already_position_open(self) -> bool:
        if self.synthetix.is_already_position_open() or self.binance.is_already_position_open():
            logger.info("MasterPositionController - Position already open")
            return True
        return False

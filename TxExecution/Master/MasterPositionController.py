import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from TxExecution.Binance.BinancePositionController import BinancePositionController
from TxExecution.ByBit.ByBitPositionController import ByBitPositionController
from TxExecution.Synthetix.SynthetixPositionController import SynthetixPositionController
from TxExecution.Master.MasterPositionControllerUtils import *
from pubsub import pub
from GlobalUtils.logger import logger

class MasterPositionController:
    def __init__(self):
        self.synthetix = SynthetixPositionController()
        self.binance = BinancePositionController()
        self.bybit = ByBitPositionController()
        pub.subscribe(self.execute_trades, 'opportunity_found')

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

            # Attempt to execute trades on specified exchanges
            for exchange_name in [long_exchange, short_exchange]:
                execute_trade_method = getattr(self, exchange_name.lower()).execute_trade
                position_data = execute_trade_method(
                    opportunity, 
                    is_long=exchange_name == long_exchange, 
                    trade_size=trade_size
                )
                
                # Debugging: Log response from each trade execution
                logger.info(f"MasterPositionController - {exchange_name} trade execution response: {position_data}")

                if position_data:  # Ensure the trade was executed successfully
                    position_data_dict[exchange_name] = position_data

            # Ensure trades were executed on both exchanges
            if len(position_data_dict) == 2:
                pub.sendMessage('position_opened', position_data=position_data_dict)
                logger.info("MasterPositionController - Trades executed successfully for opportunity.")
            else:
                self.cancel_all_trades()  # Ensure this method properly cancels any partially executed trades
                missing_exchanges = set([long_exchange, short_exchange]) - set(position_data_dict.keys())
                logger.error(f"MasterPositionController - Failed to execute trades on all required exchanges. Missing: {missing_exchanges}. Cancelling trades.")

        except Exception as e:
            logger.error(f"MasterPositionController - Failed to process trades for opportunity. Error: {e}")
            self.cancel_all_trades()

    def cancel_all_trades(self):
        self.synthetix.close_all_positions()
        self.binance.close_all_positions()
        pub.sendMessage('position_closed')

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_trade_size(self, opportunity) -> float:
        try:
            collateral_amounts = self.get_available_collateral_by_exchange()
            trade_size = adjust_collateral_allocation(
                collateral_amounts,
                opportunity['long_exchange'],
                opportunity['short_exchange'])
            
            logger.info(f"MasterPositionController - Trade size calculated: {trade_size}")
            return trade_size
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to calculate trade size for opportunity. Error: {e}")
            return 0.0


    def get_available_collateral_by_exchange(self):
        try:
            synthetix_collateral = self.synthetix.get_available_collateral()
            binance_collateral = self.binance.get_available_collateral()
            bybit_collateral = self.bybit.get_available_collateral()
            
            collateral = {
                "Synthetix": synthetix_collateral,
                "Binance": binance_collateral,
                "Bybit": bybit_collateral
            }
            logger.info("MasterPositionController - Successfully retrieved available collateral from all exchanges.")
            return collateral
        except Exception as e:
            logger.error(f"MasterPositionController - Failed to get available collateral by exchange. Error: {e}")
            return None

    def is_already_position_open(self) -> bool:
        if self.synthetix.is_already_position_open() or self.binance.is_already_position_open() or self.bybit.is_already_position_open():
            logger.info("MasterPositionController - Posotion already open")
            return True
        return False



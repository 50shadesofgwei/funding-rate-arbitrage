from APICaller.GMX.GMXCallerUtils import *
from TxExecution.GMX.GMXPositionControllerUtils import *
from gmx_python_sdk.scripts.v2.order.order_argument_parser import (
    OrderArgumentParser
)
from gmx_python_sdk.scripts.v2.order.create_increase_order import IncreaseOrder
from gmx_python_sdk.scripts.v2.order.create_decrease_order import DecreaseOrder
from gmx_python_sdk.scripts.v2.get.get_open_positions import GetOpenPositions
from gmx_python_sdk.scripts.v2.gmx_utils import *
set_paths()

class GMXPositionController:
    def __init__(self):
        self.config = ARBITRUM_CONFIG_OBJECT
        self.config.set_config('/Users/jfeasby/SynthetixFundingRateArbitrage/config.yaml')

    def execute_trade(self, opportunity: dict, is_long: bool, trade_size: float):
        try:
            symbol = opportunity['symbol']
            parameters = get_params_object_from_opportunity_dict(
                opportunity,
                is_long,
                trade_size
            )
            order_parameters = OrderArgumentParser(
                    self.config,
                    is_increase=True
                ).process_parameters_dictionary(
                    parameters
            )

            IncreaseOrder(
                config=self.config,
                market_key=order_parameters['market_key'],
                collateral_address=order_parameters['start_token_address'],
                index_token_address=order_parameters['index_token_address'],
                is_long=order_parameters['is_long'],
                size_delta=order_parameters['size_delta'],
                initial_collateral_delta_amount=(
                    order_parameters['initial_collateral_delta']
                ),
                slippage_percent=order_parameters['slippage_percent'],
                swap_path=order_parameters['swap_path'],
                debug_mode=True
            )

        except Exception as e:
            logger.error(f'GMXPositionController - Failed to execute trade for symbol {symbol}. Error: {e}')
            return None

    def close_position(self, symbol: str, reason: str = None):
        out_token = "USDC"
        slippage_percent = 0.003
        amount_of_position_to_close = 1
        amount_of_collateral_to_remove = 1

        positions = self.get_open_positions(self.config)
        position = filter_positions_by_symbol(positions, symbol)
        is_long = position['is_long']

        order_parameters = transform_open_position_to_order_parameters(
            self.config,
            positions,
            symbol,
            is_long,
            slippage_percent,
            out_token,
            amount_of_position_to_close,
            amount_of_collateral_to_remove)


        DecreaseOrder(
            config=self.config,
            market_key=order_parameters['market_key'],
            collateral_address=order_parameters['collateral_address'],
            index_token_address=order_parameters['index_token_address'],
            is_long=order_parameters['is_long'],
            size_delta=order_parameters['size_delta'],
            initial_collateral_delta_amount=(
                order_parameters['initial_collateral_delta']
            ),
            slippage_percent=order_parameters['slippage_percent'],
            swap_path=order_parameters['swap_path'],
            debug_mode=True
        )

    ######################
    ### READ FUNCTIONS ###
    ######################

    def get_open_positions(self) -> dict:
        try:
            address = '0xa6D1FEda6fc70680816eF6A23faf5e454e2f9C09'
            positions = GetOpenPositions(config=self.config, address=address).get_data()

            if len(positions) > 0:
                return positions
            else:
                return None

        except Exception as e:
            logger.error(f"GMXPositionController - Failed to get open positions: {e}")
            return None


    def is_already_position_open(self) -> bool:
        try:
            address = ARBITRUM_CONFIG_OBJECT.user_wallet_address
            positions = GetOpenPositions(config=ARBITRUM_CONFIG_OBJECT, address=address).get_data()
            if len(positions) > 0:
                return True
            else:
                return False

        except KeyError as ke:
            logger.error(f"GMXPositionController - KeyError while checking if position is open: {ke}")
            return None
        except TypeError as te:
            logger.error(f"GMXPositionController - TypeError while checking if position is open: {te}")
            return None
        except Exception as e:
            logger.error(f"GMXPositionController - Error while checking if position is open: {e}", exc_info=True)
            return None


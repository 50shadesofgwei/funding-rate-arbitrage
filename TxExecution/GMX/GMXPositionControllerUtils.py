from GlobalUtils.logger import *
from gmx_python_sdk.scripts.v2.gmx_utils import *
from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from decimal import Decimal

def get_params_object_from_opportunity_dict(opportunity: dict, is_long: bool, trade_size: float) -> dict:
    try:
        symbol = opportunity['symbol']
        parameters = {
            "chain": 'arbitrum',
            "index_token_symbol": symbol,
            "collateral_token_symbol": symbol,
            "start_token_symbol": "USDC",
            "is_long": is_long,
            "size_delta_usd": trade_size,
            "leverage": 1,
            "slippage_percent": 0.003
        }
        return parameters
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to build a parameters object from opportunity. Error: {e}')
        return None

def transform_open_position_to_order_parameters(
    config,
    positions: dict,
    market_symbol: str,
    is_long: bool,
    slippage_percent: float,
    out_token,
    amount_of_position_to_close,
    amount_of_collateral_to_remove
):

    direction = "short"
    if is_long:
        direction = "long"

    position_dictionary_key = "{}_{}".format(
        market_symbol.upper(),
        direction
    )

    try:
        raw_position_data = positions[position_dictionary_key]
        gmx_tokens = get_tokens_address_dict(config.chain)

        collateral_address = find_dictionary_by_key_value(
            gmx_tokens,
            "symbol",
            raw_position_data['collateral_token']
        )["address"]

        gmx_tokens = get_tokens_address_dict(config.chain)

        index_address = find_dictionary_by_key_value(
            gmx_tokens,
            "symbol",
            raw_position_data['market_symbol'][0]
        )
        out_token_address = find_dictionary_by_key_value(
            gmx_tokens,
            "symbol",
            out_token
        )['address']
        markets = Markets(config=config).get_available_markets()

        swap_path = []

        if collateral_address != out_token_address:
            swap_path = determine_swap_route(
                markets,
                collateral_address,
                out_token_address
            )[0]
        size_delta = int(int(
            (Decimal(raw_position_data['position_size']) * (Decimal(10)**30))
        ) * amount_of_position_to_close)

        return {
            "chain": config.chain,
            "market_key": raw_position_data['market'],
            "collateral_address": collateral_address,
            "index_token_address": index_address["address"],
            "is_long": raw_position_data['is_long'],
            "size_delta": size_delta,
            "initial_collateral_delta": int(int(
                raw_position_data['inital_collateral_amount']
            ) * amount_of_collateral_to_remove
            ),
            "slippage_percent": slippage_percent,
            "swap_path": swap_path
        }
    except KeyError:
        raise Exception(
            "Couldn't find a {} {} for given user".format(
                market_symbol, direction
            )
        )

def filter_positions_by_symbol(positions: dict, symbol: str) -> dict:
    try:
        filtered_data = {}
        for key, value in positions.items():
            if 'market_symbol' in value and symbol in value['market_symbol']:
                filtered_data[key] = value
        return filtered_data
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to filter positions by symbol. Symbol: {symbol}, Error: {e}')
        return None

from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from gmx_python_sdk.scripts.v2.gmx_utils import *
from gmx_python_sdk.scripts.v2.get.get_markets import Markets
from decimal import Decimal, getcontext
from APICaller.GMX.GMXCallerUtils import ARBITRUM_CONFIG_OBJECT
from APICaller.GMX.GMXContractUtils import *
from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory
from APICaller.GMX.GMXContractUtils import get_claimable_funding_amount, get_index_token_address_for_symbol


def get_params_object_from_opportunity_dict(opportunity: dict, is_long: bool, trade_size: float, leverage: int) -> dict:
    try:
        symbol = opportunity['symbol']
        parameters = {
            "chain": 'arbitrum',
            "index_token_symbol": symbol,
            "collateral_token_symbol": symbol,
            "start_token_symbol": "USDC",
            "is_long": is_long,
            "size_delta_usd": trade_size,
            "leverage": leverage,
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

        getcontext().prec = 50
        size = Decimal(str(raw_position_data['position_size']))
        delta_factor = Decimal('10') ** 30
        size_delta = int(
            size * delta_factor * amount_of_position_to_close
        )

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
    except KeyError as ke:
        logger.error(f"GMXPositionControllerUtils - Couldn't find a {market_symbol} {direction} for wallet address. Error: {ke}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"GMXPositionControllerUtils - Failed to transform open position to order parameters. Error: {e}", exc_info=True)
        return None
        
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

def get_arbitrum_usdc_balance():
    try:
        provider = os.getenv('ARBITRUM_PROVIDER_RPC')
        web3_obj = Web3(Web3.HTTPProvider(provider))
        usdc_address = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'
        with open('GlobalUtils/ABIs/USDCArbitrum.json', 'r') as abi_file:
            token_abi = json.load(abi_file)
        
        contract = web3_obj.eth.contract(address=usdc_address, abi=token_abi)
        balance = contract.functions.balanceOf(ARBITRUM_CONFIG_OBJECT.user_wallet_address).call()
        decimals = 6
        human_readable_balance = balance / (10 ** decimals)

        return human_readable_balance
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to fetch USDC balance for address {ARBITRUM_CONFIG_OBJECT.user_wallet_address}. Error: {e}')
        return None

def get_claimable_funding_for_symbol(symbol: str) -> dict:
    try:
        market = GMXMarketDirectory.get_market_key_for_symbol(symbol)
        index_token_address = get_index_token_address_for_symbol(symbol)
        token_decimals = get_decimals_for_symbol(symbol)
        account = ARBITRUM_CONFIG_OBJECT.user_wallet_address
        usdc_token_address = '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'

        claimable_usdc = get_claimable_funding_amount(
            market,
            usdc_token_address,
            account
        )
        claimable_usdc = claimable_usdc / 10**6

        claimable_token = get_claimable_funding_amount(
            market,
            index_token_address,
            account
        )
        claimable_token = claimable_token / 10**token_decimals

        claimable_amounts_by_token = {
            symbol: claimable_token,
            'USDC': claimable_usdc
        }

        return claimable_amounts_by_token

    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to fetch claimable funding amounts for symbol {symbol}. Error: {e}')
        return None

def get_pnl_from_position_object(position: dict) -> float:
    try:
        initial_collateral_amount_usd = float(position['inital_collateral_amount_usd'][0])
        percent_profit = float(position['percent_profit'] / 100)
        percent_profit = percent_profit * -1
        pnl_usd = initial_collateral_amount_usd * percent_profit

        return pnl_usd
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to calculate pnl from position object. Position: {position}. Error: {e}')
        return None


from gmx_python_sdk.scripts.v2.gmx_utils import *
from gmx_python_sdk.scripts.v2.get.get import GetData
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from APICaller.GMX.GMXCallerUtils import ARBITRUM_CONFIG_OBJECT
from GlobalUtils.logger import logger
from decimal import Decimal, getcontext
getcontext().prec = 50

DATASTORE_CONTRACT_OBJECT = get_datastore_contract(ARBITRUM_CONFIG_OBJECT)
READER_CONTRACT_OBJECT = get_reader_contract(ARBITRUM_CONFIG_OBJECT)

DATASTORE_ADDRESS = '0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8'

FUNDING_FACTOR = create_hash_string("FUNDING_FACTOR")
FUNDING_EXPONENT_FACTOR = create_hash_string("FUNDING_EXPONENT_FACTOR")
FUNDING_INCREASE_FACTOR_PER_SECOND = create_hash_string("FUNDING_INCREASE_FACTOR_PER_SECOND")
FUNDING_DECREASE_FACTOR_PER_SECOND = create_hash_string("FUNDING_DECREASE_FACTOR_PER_SECOND")
MIN_FUNDING_FACTOR_PER_SECOND_LIMIT = create_hash_string("MIN_FUNDING_FACTOR_PER_SECOND_LIMIT")
MAX_FUNDING_FACTOR_PER_SECOND_LIMIT = create_hash_string("MAX_FUNDING_FACTOR_PER_SECOND_LIMIT")
THRESHOLD_FOR_STABLE_FUNDING = create_hash_string("THRESHOLD_FOR_STABLE_FUNDING")
THRESHOLD_FOR_DECREASE_FUNDING = create_hash_string("THRESHOLD_FOR_DECREASE_FUNDING")

OPTIMAL_USAGE_FACTOR = create_hash_string("OPTIMAL_USAGE_FACTOR")
BASE_BORROWING_FACTOR = create_hash_string("BASE_BORROWING_FACTOR")
BELOW_OPTIMAL_USAGE_BORROWING_FACTOR = create_hash_string("BELOW_OPTIMAL_USAGE_BORROWING_FACTOR")
BORROWING_FACTOR = create_hash_string("BORROWING_FACTOR")
BORROWING_EXPONENT_FACTOR = create_hash_string("BORROWING_EXPONENT_FACTOR") 

ACCOUNT_POSITION_LIST = create_hash_string("ACCOUNT_POSITION_LIST")
CLAIMABLE_FEE_AMOUNT = create_hash_string("CLAIMABLE_FEE_AMOUNT")
DECREASE_ORDER_GAS_LIMIT = create_hash_string("DECREASE_ORDER_GAS_LIMIT")
DEPOSIT_GAS_LIMIT = create_hash_string("DEPOSIT_GAS_LIMIT")

WITHDRAWAL_GAS_LIMIT = create_hash_string("WITHDRAWAL_GAS_LIMIT")

EXECUTION_GAS_FEE_BASE_AMOUNT = create_hash_string("EXECUTION_GAS_FEE_BASE_AMOUNT")
EXECUTION_GAS_FEE_MULTIPLIER_FACTOR = create_hash_string("EXECUTION_GAS_FEE_MULTIPLIER_FACTOR")
INCREASE_ORDER_GAS_LIMIT = create_hash_string("INCREASE_ORDER_GAS_LIMIT")
MAX_OPEN_INTEREST = create_hash_string("MAX_OPEN_INTEREST")
MAX_PNL_FACTOR_FOR_TRADERS = create_hash_string("MAX_PNL_FACTOR_FOR_TRADERS")
MAX_PNL_FACTOR_FOR_DEPOSITS = create_hash_string("MAX_PNL_FACTOR_FOR_DEPOSITS")
MAX_PNL_FACTOR_FOR_WITHDRAWALS = create_hash_string("MAX_PNL_FACTOR_FOR_WITHDRAWALS")
MIN_ADDITIONAL_GAS_FOR_EXECUTION = create_hash_string("MIN_ADDITIONAL_GAS_FOR_EXECUTION")
OPEN_INTEREST_IN_TOKENS = create_hash_string("OPEN_INTEREST_IN_TOKENS")
OPEN_INTEREST = create_hash_string("OPEN_INTEREST")
OPEN_INTEREST_RESERVE_FACTOR = create_hash_string(
    "OPEN_INTEREST_RESERVE_FACTOR"
)
POOL_AMOUNT = create_hash_string("POOL_AMOUNT")
RESERVE_FACTOR = create_hash_string("RESERVE_FACTOR")
SINGLE_SWAP_GAS_LIMIT = create_hash_string("SINGLE_SWAP_GAS_LIMIT")
SWAP_ORDER_GAS_LIMIT = create_hash_string("SWAP_ORDER_GAS_LIMIT")
VIRTUAL_TOKEN_ID = create_hash_string("VIRTUAL_TOKEN_ID")

MIN_COLLATERAL_FACTOR = create_hash_string("MIN_COLLATERAL_FACTOR")
MIN_COLLATERAL_USD = create_hash_string("MIN_COLLATERAL_USD")
MIN_POSITION_SIZE_USD = create_hash_string("MIN_POSITION_SIZE_USD")


def minCollateralFactorKey(market: str):
    return create_hash(["bytes32", "address"], [MIN_COLLATERAL_FACTOR, market])

def minCollateralUsdKey(market: str):
    return create_hash(["bytes32", "address"], [MIN_COLLATERAL_USD, market])

def accountPositionListKey(account):
    return create_hash(
        ["bytes32", "address"],
        [ACCOUNT_POSITION_LIST, account]
    )

def funding_factor_key(market: str):
    return create_hash(["bytes32", "address"], [FUNDING_FACTOR, market])

def funding_exponent_factor_key(market: str):
    return create_hash(["bytes32", "address"], [FUNDING_EXPONENT_FACTOR, market])

def funding_increase_factor_key(market: str):
    return create_hash(["bytes32", "address"], [FUNDING_INCREASE_FACTOR_PER_SECOND, market])

def funding_decrease_factor_key(market: str):
    return create_hash(["bytes32", "address"], [FUNDING_DECREASE_FACTOR_PER_SECOND, market])

def threshold_for_stable_funding_key(market: str):
    return create_hash(["bytes32", "address"], [THRESHOLD_FOR_STABLE_FUNDING, market])

def threshold_for_decrease_funding_key(market: str):
    return create_hash(["bytes32", "address"], [THRESHOLD_FOR_DECREASE_FUNDING, market])

def max_funding_factor_key(market: str):
    return create_hash(["bytes32", "address"], [MAX_FUNDING_FACTOR_PER_SECOND_LIMIT, market])


def open_interest_in_tokens_key(market: str, collateral_token: str, is_long: bool):
  return create_hash(
    ["bytes32", "address", "address", "bool"],
    [OPEN_INTEREST_IN_TOKENS, market, collateral_token, is_long]
  )


def claimable_fee_amount_key(market: str, token: str):
    return create_hash(
        ["bytes32", "address", "address"],
        [CLAIMABLE_FEE_AMOUNT, market, token]
    )


def decrease_order_gas_limit_key():
    return DECREASE_ORDER_GAS_LIMIT


def deposit_gas_limit_key():
    return DEPOSIT_GAS_LIMIT


def execution_gas_fee_base_amount_key():
    return EXECUTION_GAS_FEE_BASE_AMOUNT


def execution_gas_fee_multiplier_key():
    return EXECUTION_GAS_FEE_MULTIPLIER_FACTOR


def increase_order_gas_limit_key():
    return INCREASE_ORDER_GAS_LIMIT


def min_additional_gas_for_execution_key():
    return MIN_ADDITIONAL_GAS_FOR_EXECUTION


def max_open_interest_key(market: str,
                          is_long: bool):

    return create_hash(
        ["bytes32", "address", "bool"],
        [MAX_OPEN_INTEREST, market, is_long]
    )


def open_interest_in_tokens_key(
    market: str,
    collateral_token: str,
    is_long: bool
):
    return create_hash(
        ["bytes32", "address", "address", "bool"],
        [OPEN_INTEREST_IN_TOKENS, market, collateral_token, is_long]
    )


def open_interest_key(
    market: str,
    collateral_token: str,
    is_long: bool
):
    return create_hash(
        ["bytes32", "address", "address", "bool"],
        [OPEN_INTEREST, market, collateral_token, is_long]
    )


def open_interest_reserve_factor_key(
    market: str,
    is_long: bool
):
    return create_hash(
        ["bytes32", "address", "bool"],
        [OPEN_INTEREST_RESERVE_FACTOR, market, is_long]
    )


def pool_amount_key(
    market: str,
    token: str
):
    return create_hash(
        ["bytes32", "address", "address"],
        [POOL_AMOUNT, market, token]
    )


def reserve_factor_key(
    market: str,
    is_long: bool
):
    return create_hash(
        ["bytes32", "address", "bool"],
        [RESERVE_FACTOR, market, is_long]
    )


def single_swap_gas_limit_key():
    return SINGLE_SWAP_GAS_LIMIT


def swap_order_gas_limit_key():
    return SWAP_ORDER_GAS_LIMIT


def virtualTokenIdKey(token: str):
    return create_hash(["bytes32", "address"], [VIRTUAL_TOKEN_ID, token])


def withdraw_gas_limit_key():
    return WITHDRAWAL_GAS_LIMIT


class GetFundingCalculationData(GetData):
    def __init__(self, config):
        super().__init__(config)
        self.config = config

    def _get_data_processing(self):

        open_interest = OpenInterest(
            config=self.config
        ).get_data(to_json=False)

        # define empty lists to pass to zip iterater later on
        mapper = []
        output_list = []
        long_interest_usd_list = []
        short_interest_usd_list = []

        # loop markets
        for market_key in self.markets.info:
            symbol = self.markets.get_market_symbol(market_key)
            index_token_address = self.markets.get_index_token_address(market_key)
            self._get_token_addresses(market_key)

            output = self._get_oracle_prices(market_key, index_token_address)

            mapper.append(symbol)
            output_list.append(output)
            long_interest_usd_list.append(open_interest['long'][symbol] * 10 ** 30)
            short_interest_usd_list.append(open_interest['short'][symbol] * 10 ** 30)

            # Multithreaded call on contract for each block number
            threaded_output = execute_threading(output_list)

            for (
                output,
                long_interest_usd,
                short_interest_usd,
                symbol
            ) in zip(
                threaded_output,
                long_interest_usd_list,
                short_interest_usd_list,
                mapper
            ):

                market_info_dict = {
                    "market_token": output[0][0],
                    "index_token": output[0][1],
                    "long_token": output[0][2],
                    "short_token": output[0][3],
                    "long_borrow_fee": output[1],
                    "short_borrow_fee": output[2],
                    "is_long_pays_short": output[4][0],
                    "funding_factor_per_second": output[4][1]
                }

                long_funding_fee = get_funding_factor_per_period(
                    market_info_dict,
                    True,
                    3600 * 8,
                    long_interest_usd,
                    short_interest_usd
                )

                short_funding_fee = get_funding_factor_per_period(
                    market_info_dict,
                    False,
                    3600 * 8,
                    long_interest_usd,
                    short_interest_usd
                )

            self.output['long'][symbol] = long_funding_fee
            self.output['short'][symbol] = short_funding_fee

        return self.output

INDEX_TOKEN_ADDRESSES = {
    "BTC": '0x47904963fc8b2340414262125aF798B9655E58Cd',
    "ETH": '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
    "SOL": '0x2bcC6D6CdBbDC0a4071e48bb3B969b06B3330c07',
    "ARB": '0x912CE59144191C1204E64559FE8253a0e49E6548',
    "LINK": '0xf97f4df75117a78c1A5a0DBb814Af92458539FB4',
    "UNI": '0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0',
    "LTC": '0xB46A094Bc4B0adBD801E14b9DB95e05E28962764',
    "BNB": '0xa9004A5421372E1D83fB1f85b0fc986c912f91f3',
    "DOGE": '0xC4da4c24fd591125c3F47b340b6f4f76111883d8',
    "AVAX": '0x565609fAF65B92F7be02468acF86f8979423e514',
    "NEAR": '0x1FF7F3EFBb9481Cbd7db4F932cBCD4467144237C',
    "AAVE": '0xba5DdD1f9d7F570dc94a51479a000E3BCE967196',
    "ATOM": '0x7D7F1765aCbaF847b9A1f7137FE8Ed4931FbfEbA',
    "XRP": '0xc14e065b0067dE91534e032868f5Ac6ecf2c6868',
    "AAVE": '0xba5DdD1f9d7F570dc94a51479a000E3BCE967196',
    "OP": '0xaC800FD6159c2a2CB8fC31EF74621eB430287a5A',
    "GMX": '0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a',
    "PEPE": '0x25d887Ce7a35172C62FeBFD67a1856F20FaEbB00',
    "WIF": '0xA1b91fe9FD52141Ff8cac388Ce3F10BFDc1dE79d',
}

def get_index_token_address_for_symbol(symbol):
    return INDEX_TOKEN_ADDRESSES.get(symbol, None)

def get_min_collateral_factor(market: str) -> float:
    try:
        min_collateral_factor_key = minCollateralFactorKey(market)
        min_collateral_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(min_collateral_factor_key)
        min_collateral_factor = min_collateral_func.call()
        min_collateral_factor = min_collateral_factor / 10**30

        return min_collateral_factor
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call min_collateral_factor from datastore contract. Error: {e}')
        return None

def get_funding_exponent(market: str) -> float:
    try:
        funding_exponent_key = funding_exponent_factor_key(market)
        funding_exponent_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(funding_exponent_key)
        funding_exponent = funding_exponent_func.call()
        funding_exponent = funding_exponent / 10**30

        return funding_exponent
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_exponent from datastore contract. Error: {e}')
        return None

def get_funding_factor(market: str) -> float:
    try:
        funding_factor_key_variable = funding_factor_key(market)
        funding_factor_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(funding_factor_key_variable)
        funding_factor = funding_factor_func.call()
        funding_factor = funding_factor / 10**30

        return funding_factor
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_factor from datastore contract. Error: {e}')
        return None

def get_funding_increase_factor(market: str) -> float:
    try:
        funding_increase_factor_key_variable = funding_increase_factor_key(market)
        funding_increase_factor_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(funding_increase_factor_key_variable)
        funding_increase_factor = funding_increase_factor_func.call()
        funding_increase_factor = funding_increase_factor / 10**30

        return funding_increase_factor
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_increase_factor from datastore contract. Error: {e}')
        return None

def get_funding_decrease_factor(market: str) -> float:
    try:
        funding_decrease_factor_key_variable = funding_decrease_factor_key(market)
        funding_decrease_factor_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(funding_decrease_factor_key_variable)
        funding_decrease_factor = funding_decrease_factor_func.call()
        funding_decrease_factor = funding_decrease_factor / Decimal("10")**30
        funding_decrease_factor = float(funding_decrease_factor)

        return funding_decrease_factor
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_increase_factor from datastore contract. Error: {e}')
        return None

def get_threshold_for_stable_funding(market: str) -> float:
    try:
        threshold_for_stable_key = threshold_for_stable_funding_key(market)
        threshold_for_stable_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(threshold_for_stable_key)
        threshold_for_stable = threshold_for_stable_func.call()
        threshold_for_stable = threshold_for_stable / 10**30

        return threshold_for_stable
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_increase_factor from datastore contract. Error: {e}')
        return None

def get_threshold_for_decrease_funding(market: str) -> float:
    try:
        threshold_for_decrease_key = threshold_for_stable_funding_key(market)
        threshold_for_decrease_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(threshold_for_decrease_key)
        threshold_for_decrease = threshold_for_decrease_func.call()
        threshold_for_decrease = threshold_for_decrease / 10**30
        

        return threshold_for_decrease
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_increase_factor from datastore contract. Error: {e}')
        return None

def get_max_funding_factor_for_market(market: str) -> float:
    try:
        max_funding_factor_key_variable = max_funding_factor_key(market)
        max_funding_factor_func = DATASTORE_CONTRACT_OBJECT.functions.getUint(max_funding_factor_key_variable)
        max_funding_factor = max_funding_factor_func.call()
        max_funding_factor = max_funding_factor / 10**30
        
        return max_funding_factor
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to call funding_increase_factor from datastore contract. Error: {e}')
        return None
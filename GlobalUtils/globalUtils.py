from web3 import *
import os
from dotenv import load_dotenv
import requests
from decimal import Decimal, InvalidOperation
from enum import Enum
from GlobalUtils.logger import *


import functools
import re
import time
import json
from typing import Tuple

load_dotenv()

# app.log file path
log_path = logger.handlers[0].__dict__["baseFilename"]
NULL_ADDRESS = '0x0000000000000000000000000000000000000000'

BLOCKS_PER_DAY_BASE = 43200
BLOCKS_PER_HOUR_BASE = 1800


### Initialize Clients -> prevents double initialization
def initialize_synthetix_client():
    global GLOBAL_SYNTHETIX_CLIENT
    if GLOBAL_SYNTHETIX_CLIENT is None:
        GLOBAL_SYNTHETIX_CLIENT = get_synthetix_client()

def initialize_binance_client():
    global GLOBAL_BINANCE_CLIENT
    if GLOBAL_BINANCE_CLIENT is None:
        GLOBAL_BINANCE_CLIENT = get_binance_client()

def initialize_HMX_client():
    global GLOBAL_HMX_CLIENT
    if GLOBAL_HMX_CLIENT is None:
        GLOBAL_HMX_CLIENT = get_HMX_client()

def initialize_exchange_clients():
    initialize_binance_client()
    initialize_HMX_client()
    initialize_synthetix_client()

class EventsDirectory(Enum):
    CLOSE_ALL_POSITIONS = "close_all_positions"
    CLOSE_POSITION_PAIR = "close_position_pair"
    OPPORTUNITY_FOUND = "opportunity_found"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    TRADE_LOGGED = "trade_logged"

DECIMALS = {
    "BTC": 8,
    "ETH": 18,
    "SNX": 18,
    "SOL": 9,
    "W": 18,
    "WIF": 6,
    "ARB": 18,
    "BNB": 18,
    "ENA": 18,
    "DOGE": 8,
    "AVAX": 18,
    "PENDLE": 18,
    "NEAR": 24,
    "AAVE": 18,
    "ATOM": 6,
    "XRP": 6,
    "LINK": 18,
    "UNI": 18,
    "LTC": 8,
    "OP": 18,
    "GMX": 18,
    "PEPE": 18,
}

def get_decimals_for_symbol(symbol):
    return DECIMALS.get(symbol, None)

# TODO: Check whether client is initialized or not before calling the function in MainClass
def initialise_client() -> Web3:
    try:
        client = Web3(Web3.HTTPProvider(os.getenv('BASE_PROVIDER_RPC')))
    except Exception as e:
        logger.error(f"GlobalUtils - Error initialising Web3 client: {e}")
        return None 
    return client

def get_gas_price() -> float:
    client = initialise_client()
    if client:
        try:
            price_in_wei = client.eth.gas_price
            price_in_gwei = client.from_wei(price_in_wei, 'gwei')
            return price_in_gwei
        except Exception as e:
            logger.error(f"GlobalUtils - Error fetching gas price: {e}")
            return None
    return 0.0

def get_price_from_pyth(symbol: str):
    try:
        response = GLOBAL_SYNTHETIX_CLIENT.pyth.get_price_from_symbols([symbol])
        
        feed_id = next(iter(response['meta']))
        meta_data = response['meta'].get(feed_id, {})
        price: float = meta_data.get('price')

        if price is not None:
            return price

    except KeyError as ke:
        logger.error(f"GlobalUtils - KeyError accessing Pyth response data for {symbol}: {ke}")
        return None
    except Exception as e:
        logger.error(f"GlobalUtils - Unexpected error fetching asset price for {symbol} from Pyth: {e}")
        return None


def calculate_transaction_cost_usd(total_gas: int) -> float:
    try:
        gas_price_gwei = get_gas_price()
        eth_price_usd = get_price_from_pyth('ETH')
        gas_cost_eth = (gas_price_gwei * total_gas) / Decimal('1e9')
        transaction_cost_usd = float(gas_cost_eth) * eth_price_usd
        return transaction_cost_usd
    except (InvalidOperation, ValueError) as e:
        logger.error(f"GlobalUtils - Error calculating transaction cost: {e}")
    return 0.0

def get_asset_amount_for_given_dollar_amount(asset: str, dollar_amount: float) -> float:
    try:
        asset_price = get_price_from_pyth(asset)
        asset_amount = dollar_amount / asset_price
        return asset_amount
    except ZeroDivisionError:
        logger.error(f"GlobalUtils - Error calculating asset amount for {asset}: Price is zero")
    return 0.0

def get_dollar_amount_for_given_asset_amount(asset: str, asset_amount: float) -> float:
    try:
        asset_price = get_price_from_pyth(asset)
        dollar_amount = asset_amount * asset_price
        return dollar_amount
    except Exception as e:
        logger.error(f"GlobalUtils - Error converting asset amount to dollar amount for {asset}: {e}")
    return 0.0

def normalize_symbol(symbol: str) -> str:
    return symbol.replace('USDT', '').replace('PERP', '').replace('USD', '')

def adjust_trade_size_for_direction(trade_size: float, is_long: bool) -> float:
    try:
        return trade_size if is_long else trade_size * -1
    except Exception as e:
        logger.error(f'GlobalUtils - Failed to adjust trade size for direction, Error: {e}')

def get_base_block_number_by_timestamp(timestamp: int) -> int:
    apikey = os.getenv('BASESCAN_API_KEY')
    url = "https://api.basescan.org/api"
    params = {
        'module': 'block',
        'action': 'getblocknobytime',
        'timestamp': timestamp,
        'closest': 'before',
        'apikey': apikey
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == '1' and data.get('message') == 'OK':
            return int(data.get('result'))
        else:
            logger.info(f"GlobalUtils - Basescan API Error: {data}")
            return -1
    except requests.RequestException as e:
        print("GlobalUtils - Basescan API HTTP Request failed:", e)
        return -1

def get_base_block_number() -> int:
    try:
        client = initialise_client()
        block_number = client.eth.block_number
        return block_number
    except Exception as e:
        logger.error(f'GlobalUtils - Error while calling current block number for BASE network: {e}')
        return None

def get_binance_funding_event_schedule(current_block_number: int) -> list:
    try:
        coordination_block = 13664526
        interval_in_blocks = 14400

        intervals_since_last_event = (current_block_number - coordination_block) // interval_in_blocks
        next_funding_event = coordination_block + (intervals_since_last_event + 1) * interval_in_blocks
        next_three_funding_events = [next_funding_event + i * interval_in_blocks for i in range(3)]
        return next_three_funding_events

    except Exception as e:
        logger.error(f'GlobalUtils - Error while calling current block number for BASE network: {e}')
        return None

def normalize_funding_rate_to_8hrs(rate: float, hours: int) -> float:
    try:
        rate_per_hour = rate / hours
        normalized_rate = rate_per_hour * 8
        return normalized_rate

    except Exception as e:
        logger.error(f'GlobalUtils - Error while normalizing funding rate to 8hrs. Function inputs: rate={rate}, hours={hours} {e}')
        return None

def is_transaction_hash(tx_hash) -> bool:
    # Regular expression to match an Ethereum transaction hash
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return re.match(pattern, tx_hash) is not None

def get_milliseconds_until_given_timestamp(timestamp: int) -> int:
    current_time = int(time.time() * 1000)
    return timestamp - current_time

def get_milliseconds_until_given_timestamp_timezone(timestamp: int, shift_timezone: bool) -> int:
    current_time = int(time.time() * 1000)
    if shift_timezone:
        current_time -= time.timezone * 1000
    return timestamp - current_time

def deco_retry(retry: int = 5, retry_sleep: int = 3):
    def deco_func(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _retry = 5 if callable(retry) else retry
            _result = None
            for _i in range(1, _retry + 1):
                try:
                    _result = func(*args, **kwargs)
                    break

                except Exception as e:
                    logger.warning(f"{func.__name__}: {_i} :{e}")
                    if _i == _retry:
                        raise

                time.sleep(retry_sleep)
            return _result

        return wrapper

    return deco_func(retry) if callable(retry) else deco_func

###############################################################
#                                                             #
#  Getter and Setter Functions for files in Parent Directory  #
#                                                             #
###############################################################
FLASK_APP_SECRET_KEY = os.getenv('FLASK_APP_SECRET_KEY')


### Bot Logs
def get_app_logs() -> str | bool:
    # TODO: return logs as json (serializable) rather than str
    try:
        logs = open(log_path, "r").readlines()
    except FileNotFoundError:
        logger.error("Logs file - app.log - not found")
        return False
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return False
    else:
        return logs

def clear_logs() -> bool:
    try:
        with open(log_path, "w") as f:
            f.write("")
    except FileNotFoundError:
        logger.error("Logs file - logs.txt - not found")
        return False
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        return False
    else:
        return True


from web3 import *
import os
from dotenv import load_dotenv
import requests
from decimal import Decimal, InvalidOperation
from enum import Enum
from GlobalUtils.logger import *
from APICaller.Synthetix.SynthetixUtils import get_synthetix_client
from APICaller.Binance.binanceUtils import get_binance_client
from APICaller.HMX.HMXCallerUtils import get_HMX_client
# from APICaller.OKX.okxUtils import get_okx_trading_data_client
# from APICaller.OKX.okxUtils import get_okx_pub_client
# from APICaller.OKX.okxUtils import get_okx_account_client
# from APICaller.OKX.okxUtils import get_okx_trade_client

import functools
import re
import time

load_dotenv()

NULL_ADDRESS = '0x0000000000000000000000000000000000000000'

BLOCKS_PER_DAY_BASE = 43200
BLOCKS_PER_HOUR_BASE = 1800

# Global variables to store client instances
GLOBAL_SYNTHETIX_CLIENT = None
GLOBAL_BINANCE_CLIENT = None
GLOBAL_HMX_CLIENT = None

# GLOBAL_OKX_PUBLIC_CLIENT = get_okx_pub_client()
# GLOBAL_OKX_TRADING_DATA_CLIENT = get_okx_trading_data_client()
# GLOBAL_OKX_ACCOUNT_CLIENT = get_okx_account_client()
# GLOBAL_OKX_TRADE_CLIENT = get_okx_trade_client()

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
### Bot Settings
def check_bot_settings(bot_settings: dict) -> bool:
    try:
        settings = bot_settings['settings']
        if (settings['max_allowable_percentage_away_from_liquidation_price'] < 5)  or (settings['max_allowable_percentage_away_from_liquidation_price'] > 30):
            logger.error("MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE must be between 5 and 30")
            return False
        if (settings['trade_leverage'] > 10 ):
            logger.error("TRADE_LEVERAGE must be greater than 10")
            return False
        if (settings['percentage_capital_per_trade'] < 0 or settings['percentage_capital_per_trade'] > 100):
            logger.error("PERCENTAGE_CAPITAL_PER_TRADE must be between 0 and 100")
            return False
        if (settings['default_trade_duration_hours'] < 6 or settings['default_trade_duration_hours'] > 24):
            logger.error("DEFAULT_TRADE_DURATION_HOURS must be greater than 0")
            return False
        if (settings['default_trade_size_usd'] < 50 or settings['default_trade_size_usd'] > 1_000_000):
            logger.error("DEFAULT_TRADE_SIZE_USD must be between 50 and 1,000,000")
            return False
    except KeyError:
        logger.error("KeyError: Check whether all required settings are present")
        return False
    else:
        return True
    
def set_bot_settings(settings: json) -> bool:
    try:
        bot_settings = json.loads(settings)
        if check_bot_settings(bot_settings) \
            and check_exchange_settings(settings) \
            and check_env_settings(settings):
            json.dump(
                settings,
                open("./bot_settings.json", "w")
            )
            return True
        else:
            return False
    except FileNotFoundError:
        logger.error("Settings file - bot_settings.json - not found")
        return False
        
def get_bot_settings() -> dict | None:
    try:
        settings = json.loads(
            open("./bot_settings.json", "r").read()
        )
    except FileNotFoundError:
        logger.error("Settings file - bot_settings.json - not found")
        return None
    except json.JSONDecodeError:
        logger.error("Error decoding settings file")
        return None
    else:
        if check_bot_settings(settings) \
            and check_exchange_settings(settings) \
            and check_env_settings(settings):
            return settings
        else:
            return None

### Exchange Settings
def check_exchange_settings(bot_settings: dict) -> bool:
    """
    Make sure the settings file include:
        ```
        "target_exchanges": [
            {"exchange": "Synthetix", "is_target": true},
            {"exchange": "Binance", "is_target": true},
            ...
        ```
    and 
        ```"
        target_tokens": [
            {"token": "BTC", "is_target": true},
            {"token": "ETH", "is_target": true},
            ...
        ```
    
    TODO: Edit the values of valid_exchanges in case of errors.
    """
    valid_exchanges = ["Synthetix", "Binance", "ByBit", "HMX", "GMX", "OKX"]
    valid_tokens = ['BTC', 'ETH', 'SNX', 'SOL', 'W', 'WIF', 'ARB', 'BNB', 'ENA', 'DOGE', 'AVAX', 'PENDLE', 'NEAR', 'AAVE', 'ATOM', 'LINK', 'UNI', 'LTC', 'OP', 'GMX', 'PEPE']
    try:
        exchange_settings = bot_settings["target_exchanges"]
        for target_exchange in exchange_settings:
            if target_exchange["exchange"] not in valid_exchanges:
                return False
            if type(target_exchange["is_target"]) is not bool:
                return False
    except KeyError as error:    # TODO: Remove print statements
        print("Key error ", error)
        return False
    try:
        token_settings = bot_settings["target_tokens"]
        for token_setting in token_settings:
            if token_setting["token"] not in valid_tokens:
                return False
            if type(token_setting["is_target"]) is not bool:
                return False
    except KeyError as error:
        print("Key error ", error)
        return False
    
    return True

def set_exchange_settings(settings: json) -> bool:
    try:
        bot_settings = settings.load(settings)
        if check_exchange_settings(bot_settings):
            json.dump(
                bot_settings, 
                open("./bot_settings.json", "w")
            )
    except FileNotFoundError:
        logger.error("Settings file - bot_settings.json - not found")
        return False

### Env Settings related to bot_settings.json
def check_env_settings(env_settings: json) -> Tuple[bool, list]:
    """
    Validate that `["base_provider_rpc", "arbitrum_provider_rpc", "chain_id_base", "address"]` are present

    Args:
    settings (list): List of required environment variable names.

    Returns:
    tuple: bool
    """
    try:
        required_vars = ["base_provider_rpc", "arbitrum_provider_rpc", "chain_id_base", "address"]
        for env in env_settings:
            if env not in required_vars:
                return False
    except KeyError as error:
        logger.log("Error setting .env file", error)
        return False
    except Exception:
        return False
    finally:
        return True

def set_env_settings(settings: json) -> bool:
    """
    Eg: Required settings:
    ```
    ["base_provider_rpc": "https://sepolia.base.org",
     "arbitrum_provider_rpc": "https://arb-mainnet.g.alchemy.com/v2/7MDAAJvIub6mc2uHF1VWx7-W68UBYoET",
     "chain_id_base": 421614,
     "address":"0x..."
    ]
    ```
    """
    try:
        env_settings = settings["env_settings"] 
        if check_env_settings(env_settings):
            # Load existing .env file
            dotenv_path = ".env"
            load_dotenv()

            set_key(dotenv_path, "BASE_PROVIDER_RPC", settings["base_provider_rpc"])
            set_key(dotenv_path, "ARBITRUM_PROVIDER_RPC", settings["arbitrum_provider_rpc"])
            set_key(dotenv_path, "CHAIN_ID_BASE", str(settings["chain_id_base"]))
            set_key(dotenv_path, "ADDRESS", settings["address"])
            
            # Reload the environment variables
            load_dotenv(dotenv_path, override=True)
            return True
        return False
    except Exception as e:
        print(f"Error setting environment variables: {str(e)}")
        return False

### Private and API key settings | NOT VISIBLE IN CLIENT
def set_synthetix_config() -> bool:
    print("synth config")

def set_binance_config(BINANCE_API_KEY, BINANCE_API_SECRET) -> bool:
    """
    Sets .env file's `BINANCE_API_KEY` and `BINANCE_API_SECRET`
    """
    print("binance config")


def set_bybit_config() -> bool:
    """
    Sets .env file's `BINANCE_API_KEY` and `BINANCE_API_SECRET`
    """
    print("bybit config")
    

def set_hmx_config() -> bool:
    """
    Communicates with config.yaml file
    """
    print("hmx config")

def set_okx_config() -> bool:
    print("okx config")
    

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


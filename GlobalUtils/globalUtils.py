from web3 import *
import os
from dotenv import load_dotenv
import requests
from decimal import Decimal, InvalidOperation
from enum import Enum
from GlobalUtils.logger import *
from synthetix import Synthetix
from APICaller.Synthetix.SynthetixUtils import get_synthetix_client

load_dotenv()

BLOCKS_PER_DAY_BASE = 43200
BLOCKS_PER_HOUR_BASE = 1800

GLOBAL_SYNTHETIX_CLIENT = get_synthetix_client()

class EventsDirectory(Enum):
    CLOSE_ALL_POSITIONS = "close_all_positions"
    CLOSE_POSITION_PAIR = "close_position_pair"
    OPPORTUNITY_FOUND = "opportunity_found"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    TRADE_LOGGED = "trade_logged"

def initialise_client() -> Web3:
    try:
        client = Web3(Web3.HTTPProvider(os.getenv('BASE_PROVIDER_RPC')))
    except Exception as e:
        logger.info(f"GlobalUtils - Error initialising Web3 client: {e}")
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
            logger.info(f"GlobalUtils - Error fetching gas price: {e}")
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
        logger.info(f"GlobalUtils - Error calculating asset amount for {asset}: Price is zero")
    return 0.0

def get_dollar_amount_for_given_asset_amount(asset: str, asset_amount: float) -> float:
    try:
        asset_price = get_price_from_pyth(asset)
        dollar_amount = asset_amount * asset_price
        return dollar_amount
    except Exception as e:
        logger.info(f"GlobalUtils - Error converting asset amount to dollar amount for {asset}: {e}")
    return 0.0

def normalize_symbol(symbol: str) -> str:
    return symbol.replace('USDT', '').replace('PERP', '')

def adjust_trade_size_for_direction(trade_size: float, is_long: bool) -> float:
    return trade_size if is_long else -trade_size

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

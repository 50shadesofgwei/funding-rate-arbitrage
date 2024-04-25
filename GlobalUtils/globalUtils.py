from web3 import *
import os
from dotenv import load_dotenv
import requests
from decimal import Decimal, InvalidOperation
from enum import Enum
from GlobalUtils.logger import *

load_dotenv()

BLOCKS_PER_DAY_BASE = 43200

class EventsDirectory(Enum):
    CLOSE_ALL_POSITIONS = "close_positions"
    OPPORTUNITY_FOUND = "opportunity_found"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    TRADE_LOGGED = "trade_logged"

class MarketDirectory(Enum):
    ETH = {
        'market_id': 100,
        'symbol': 'ETH'
    }

    BTC = {
        'market_id': 200,
        'symbol': 'BTC'
    }

    def get_market_id(symbol: str) -> int:
        for market in MarketDirectory:
            if market.value['symbol'] == symbol:
                return market.value['market_id']
        raise ValueError(f"GlobalUtils - Market symbol '{symbol}' not found.")

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

def get_asset_price(asset: str) -> float:
    api_key = os.getenv('COINGECKO_API_KEY')
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={asset}&vs_currencies=usd&x_cg_demo_api_key={api_key}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"API response data for {asset}: {data}")
            return data[asset]['usd']
        else:
            logger.info(f"API call for {asset} returned non-200 status code: {response.status_code}")
    except Exception as e:
        logger.info(f"Error fetching asset price for {asset}: {e}, URL: {url}")
    return 0.0

def calculate_transaction_cost_usd(total_gas: int) -> float:
    try:
        gas_price_gwei = get_gas_price()
        eth_price_usd = get_asset_price('ethereum')
        gas_cost_eth = (gas_price_gwei * total_gas) / Decimal('1e9')
        transaction_cost_usd = float(gas_cost_eth) * eth_price_usd
        return transaction_cost_usd
    except (InvalidOperation, ValueError) as e:
        logger.info(f"GlobalUtils - Error calculating transaction cost: {e}")
    return 0.0

def get_asset_amount_for_given_dollar_amount(asset: str, dollar_amount: float) -> float:
    try:
        asset_price = get_asset_price(asset)
        asset_amount = dollar_amount / asset_price
        return asset_amount
    except ZeroDivisionError:
        logger.info(f"GlobalUtils - Error calculating asset amount for {asset}: Price is zero")
    return 0.0

def get_dollar_amount_for_given_asset_amount(asset: str, asset_amount: float) -> float:
    try:
        asset_price = get_asset_price(asset)
        dollar_amount = asset_amount * asset_price
        return dollar_amount
    except Exception as e:
        logger.info(f"GlobalUtils - Error converting asset amount to dollar amount for {asset}: {e}")
    return 0.0

def normalize_symbol(symbol: str) -> str:
    return symbol.replace('USDT', '').replace('PERP', '')

def get_full_asset_name(symbol: str) -> str:
    asset_mapping = {
        'btc': 'bitcoin',
        'eth': 'ethereum'
    }
    return asset_mapping.get(symbol.lower(), symbol)

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

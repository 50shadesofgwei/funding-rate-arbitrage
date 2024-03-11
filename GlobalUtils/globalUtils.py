from web3 import *
import os
from dotenv import load_dotenv
import requests
from decimal import Decimal

load_dotenv()

def initialise_client() -> Web3:
    client = Web3(
        provider=Web3.HTTPProvider(os.getenv('BASE_PROVIDER_RPC'))
    )
    return client

def get_gas_price() -> float:
    client = initialise_client()
    price_in_wei = client.eth.gas_price
    price_in_gwei = client.from_wei(price_in_wei, 'gwei')

    return price_in_gwei

def get_asset_price(asset: str) -> float:
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={asset}&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data[asset]['usd']

def calculate_transaction_cost_usd(total_gas: int) -> float:
    gas_price_gwei = get_gas_price()
    eth_price_usd = get_asset_price('ethereum')
    gas_cost_eth = (gas_price_gwei * total_gas) / Decimal('1e9')
    transaction_cost_usd = float(gas_cost_eth) * eth_price_usd
    return transaction_cost_usd

def get_asset_amount_for_given_dollar_amount(asset: str, dollar_amount: float) -> float:
    asset_price = get_asset_price(asset)
    asset_amount = dollar_amount / asset_price
    return asset_amount

def get_dollar_amount_for_given_asset_amount(asset: str, asset_amount: float) -> float:
    asset_price = get_asset_price(asset)
    dollar_amount = asset_amount * asset_price
    return dollar_amount

def get_full_asset_name(symbol: str) -> str:
    asset_mapping = {
        'btc': 'bitcoin',
        'eth': 'ethereum'
    }
    return asset_mapping.get(symbol.lower(), symbol)

def get_total_available_capital() -> float:
    capital = 50000.0
    return capital

def adjust_trade_size_for_direction(trade_size: float, is_long: bool) -> float:
    return trade_size if is_long else -trade_size


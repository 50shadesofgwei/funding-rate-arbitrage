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

def get_eth_price() -> float:
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data['ethereum']['usd']

def calculate_transaction_cost_usd(total_gas: int) -> float:
    gas_price_gwei = get_gas_price()
    eth_price_usd = get_eth_price()
    gas_cost_eth = (gas_price_gwei * total_gas) / Decimal('1e9')
    transaction_cost_usd = float(gas_cost_eth) * eth_price_usd
    return transaction_cost_usd

def get_total_available_capital() -> float:
    capital = 50000.0
    return capital

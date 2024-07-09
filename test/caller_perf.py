import time
import statistics
from typing import Callable, Any
from hexbytes import *
import os
from dotenv import load_dotenv
from enum import Enum

from synthetix import *
from hmx2.hmx_client import Client as HMX
from binance.um_futures import UMFutures as Binance
from okx.PublicData import PublicAPI
from pybit.unified_trading import HTTP

load_dotenv()

TRACKING_CODE: str = '0x46756e64696e67426f7400000000000000000000000000000000000000000000'
NUM_RUNS = 5

ARBITRUM_PROVIDER_RPC = os.getenv('ARBITRUM_PROVIDER_RPC')
BASE_PROVIDER_RPC = os.getenv('BASE_PROVIDER_RPC')

def time_request(create_client_func: Callable[[], Any], request_func: Callable[[Any], Any], num_runs: int = NUM_RUNS) -> dict:
    """
    Time the request function and return statistics.

    Args:
        create_client_func (Callable[[], Any]): The function to create a client.
        request_func (Callable[[Any], Any]): The request function to time.
        num_runs (int): The number of times to run the request.

    Returns:
        dict: A dictionary containing average, min, and max times.
    """
    client = create_client_func()
    times = []
    for _ in range(num_runs):
        start_time = time.time()
        request_func(client)
        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)
        print(f"Run {_ + 1}/{num_runs}: {elapsed_time:.4f} seconds")
        time.sleep(2)
    
    return {
        "average_time": statistics.mean(times),
        "min_time": min(times),
        "max_time": max(times)
    }

def create_HMX_client():
    return HMX(rpc_url=ARBITRUM_PROVIDER_RPC)

def hmx_funding_rate_request(client):
    client.public.get_all_market_info()

def create_synthetix_client():
    return Synthetix(provider_rpc=BASE_PROVIDER_RPC, 
                     tracking_code=TRACKING_CODE)

def synthetix_funding_rate_request(client):
    client.perps.get_markets()

def create_binance_client():
    return Binance()

def binance_funding_rate_request(client):
    client.funding_rate(symbol='BTCUSDT')

def create_okx_client():
    return PublicAPI()

def okx_funding_rate_request(client):
    client.get_funding_rate(instId='BTC-USDT-SWAP')

def create_bybit_client():
    return HTTP(testnet=False)

def bybit_funding_rate_request(client):
    client.get_tickers(
                    category='linear',
                    symbol='BTCUSDT',
                    limit='1',
                    fundingInterval='1'
                )

def print_stats(service_name: str, stats: dict):
    """
    Print the statistics in a formatted way.

    Args:
        service_name (str): The name of the service.
        stats (dict): The statistics dictionary containing average, min, and max times.
    """
    print(f"{service_name} request times:")
    print(f"  Average time: {stats['average_time']:.4f} seconds")
    print(f"  Min time:     {stats['min_time']:.4f} seconds")
    print(f"  Max time:     {stats['max_time']:.4f} seconds")
    print()

if __name__ == "__main__":

    hmx_stats = time_request(create_HMX_client, hmx_funding_rate_request)
    
    synthetix_stats = time_request(create_synthetix_client, synthetix_funding_rate_request)
    
    binance_stats = time_request(create_binance_client, binance_funding_rate_request)

    okx_stats = time_request(create_okx_client, okx_funding_rate_request)

    bybit_stats = time_request(create_bybit_client, bybit_funding_rate_request)

    print_stats("HMX", hmx_stats)

    print_stats("Synthetix", synthetix_stats)

    print_stats("Binance", binance_stats)

    print_stats("Okx", binance_stats)
    
    print_stats("Bybit", binance_stats) 

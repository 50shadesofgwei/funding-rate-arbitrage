import os
from dotenv import load_dotenv
from binance.um_futures import UMFutures as Binance
load_dotenv()

def get_binance_client() -> Binance:
    api_key = str(os.getenv('BINANCE_API_KEY'))
    api_secret = str(os.getenv('BINANCE_API_SECRET'))
    client = Binance(api_key, api_secret)

    return client

GLOBAL_BINANCE_CLIENT = get_binance_client()   

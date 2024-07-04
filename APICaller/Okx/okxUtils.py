import os
from dotenv import load_dotenv
from APICaller.OKX.PublicData import okxPublicAPI
from okx.TradingData import okxTradingDataAPI

load_dotenv()

def get_okx_pub_client() -> okxPublicAPI:
    okx_pub_client = okxPublicAPI()
    return okx_pub_client

def get_okx_trading_data_client() -> okxTradingDataAPI:
    okx_trading_data_client = okxTradingDataAPI()
    return okx_trading_data_client

def set_okx_symbol(symbol) -> str:
    return f"{symbol}-USD-SWAP"
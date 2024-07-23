import os
import okx
from dotenv import load_dotenv
from okx.PublicData import PublicAPI as okxPublicAPI
from okx.TradingData import TradingDataAPI as okxTradingDataAPI
import okx.Account as Account
import okx.Trade as Trade
load_dotenv()

def get_okx_pub_client() -> okxPublicAPI:
    okx_pub_client = okxPublicAPI(flag = '0')
    return okx_pub_client

def get_okx_trading_data_client() -> okxTradingDataAPI:
    okx_trading_data_client = okxTradingDataAPI(flag = '0')
    return okx_trading_data_client

def set_okx_symbol(symbol) -> str:
    return f"{symbol}-USD-SWAP"

def get_okx_account_client() ->Account.AccountAPI:
    api_key = str(os.getenv('OKX_API_KEY'))
    secret_key = str(os.getenv('OKX_API_SECRET'))    
    passphrase = str(os.getenv('OKX_PASSPHRASE'))

    accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, False, 0) # 0 for live trading

    return accountAPI

def get_okx_trade_client() ->Trade.TradeAPI:
    api_key = str(os.getenv('OKX_API_KEY'))
    secret_key = str(os.getenv('OKX_API_SECRET'))    
    passphrase = str(os.getenv('OKX_PASSPHRASE'))

    tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, 0) # 0 for live trading

    return tradeAPI




import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.Binance.binanceUtils import BinanceEnvVars
from GlobalUtils.logger import logger
from binance.um_futures import UMFutures as Client
from binance.enums import *
from pubsub import pub
from dotenv import load_dotenv

load_dotenv()

class BinancePositionMonitor():
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret, base_url="https://testnet.binancefuture.com")



    
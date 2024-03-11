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

    def get_position_object_from_event(self, order_confirmation_object) -> dict:
        symbol = order_confirmation_object["symbol"]
        side = order_confirmation_object['side']
        size = order_confirmation_object['size']
        order_id = order_confirmation_object['order_id']
        liquidation_price = self.get_liquidation_price(order_confirmation_object["symbol"])

        return {
            'exchange': 'Binance',
            'symbol': symbol,
            'side': side,
            'size': size,
            'order_id': order_id,
            'liquidation_price': liquidation_price
        }

    def get_liquidation_price(self, symbol: str) -> float:
        response = self.client.get_position_risk(symbol)
        liquidation_price = float(response['liquidationPrice'])

        return liquidation_price


    
from APICaller.Binance.binanceUtils import BinanceEnvVars
from binance.client import Client
from binance.enums import *
from pubsub import pub
import os
from dotenv import load_dotenv

load_dotenv()

class BinancePositionController:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret)

    def open_position(self, position_to_open):
        self.client.futures_create_order(
            symbol=position_to_open.symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=position_to_open.quantity)

    def get_available_collateral(self) -> float:
        account_details = self.client.get_margin_account()
        for asset in account_details['userAssets']:
            if asset['asset'] == 'USDT':
                return float(asset['free'])
        return 0.0

    def is_already_position_open(self) -> bool:
        positions = self.client.futures_position_information()
        for position in positions:
            if float(position['positionAmt']) != 0:
                return True
        return False


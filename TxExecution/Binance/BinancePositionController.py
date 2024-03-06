from APICaller.Binance.binanceUtils import BinanceEnvVars
from APICaller.master.MasterUtils import TARGET_TOKENS
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
        self.leverage = int(os.getenv('TRADE_LEVERAGE'))
        self.set_leverage_for_all_assets(self, TARGET_TOKENS)

    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        order = self.get_order_from_opportunity(opportunity, is_long)
        order_with_amount = self.add_amount_to_order(order, trade_size)
        self.client.futures_create_order(
            symbol=order_with_amount['symbol'],
            side=order_with_amount['side'],
            type=order_with_amount['type'],
            quantity=order_with_amount['amount'])

    def get_order_from_opportunity(self, opportunity, is_long: bool):
        side = SIDE_BUY if is_long else SIDE_SELL
        order_without_amount = {
            'symbol': opportunity['symbol'] + 'USDT',
            'side': side,
            'type': ORDER_TYPE_MARKET,
            'quantity': 0.0
        }
        return order_without_amount

    def add_amount_to_order(self, order_without_amount, amount: float):
        order_with_amount = order_without_amount.copy()
        order_with_amount['quantity'] = amount
        return order_with_amount

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

    def set_leverage_for_all_assets(self, tokens):
        for token in tokens:
            if token["is_target"]:
                symbol = token["token"] + "USDT"
                self.client.futures_change_leverage(
                    symbol=symbol,
                    leverage=self.leverage,
                )

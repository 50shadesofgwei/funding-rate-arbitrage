from pybit.unified_trading import HTTP
from APICaller.ByBit.ByBitUtils import *
from pubsub import pub
import os
from dotenv import load_dotenv
import requests
from GlobalUtils.globalUtils import *
from APICaller.master.MasterUtils import TARGET_TOKENS

load_dotenv()

class ByBitPositionController:
    
    def __init__(self):
        self.client = get_ByBit_client()
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        self.leverage = os.getenv('TRADE_LEVERAGE')
        self.set_leverage_for_all_assets(TARGET_TOKENS)

    def execute_trade(self, opportunity, is_long: bool, trade_size: float):
        side = self.get_side(is_long)
        full_asset_name = get_full_asset_name(opportunity['symbol'])
        trade_size_in_asset = get_asset_amount_for_given_dollar_amount(full_asset_name, trade_size)
        self.client.place_order(
            category="linear",
            symbol=opportunity['symbol'] + 'USDT',
            side=side,
            orderType="Market",
            qty=trade_size_in_asset,
        )

    def close_position(self):
        self.client.cancel_order()

    def is_already_position_open(self) -> bool:
        url = "https://api.bybit.com/private/linear/position/list"
        headers = {
            "X-Api-Key": self.api_key,
            "X-Api-Secret": self.api_secret
        }
        response = requests.get(url, headers=headers)
        positions = response.json().get('result', [])
        
        for position in positions:
            if position.get('size', 0) > 0:
                return True
        return False

    def get_available_collateral(self) -> float:
        usdt_collateral = self.client.get_coin_balance(accountType="UNIFIED",coin="USDT")
        collateral_amount = usdt_collateral["result"]["balance"]["walletBalance"]
        return collateral_amount

    def get_side(is_long: bool) -> str:
        if is_long:
            side = 'Buy'
            return side
        else:
            side = 'Sell'
            return side

    def set_leverage_for_all_assets(self, tokens):
        for token in tokens:
            if token["is_target"]:
                symbol = token["token"] + "USDT"
                self.client.set_leverage(
                    category="linear",
                    symbol=symbol,
                    buyLeverage=self.leverage,
                    sellLeverage=self.leverage
                )

    
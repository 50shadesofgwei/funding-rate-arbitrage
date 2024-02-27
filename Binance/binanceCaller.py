from binanceUtils import BinanceEnvVars
from binance.client import Client
from binance.enums import *


class Binance:
    def __init__(self):
        api_key = BinanceEnvVars.API_KEY.get_value()
        api_secret = BinanceEnvVars.API_SECRET.get_value()
        self.client = Client(api_key, api_secret)

    def get_funding_rate(self, symbol: str):
        futures_funding_rate = self.client.futures_funding_rate(symbol=symbol)
        return futures_funding_rate[-1]

    def execute_trade(self, symbol, side, quantity, order_type=ORDER_TYPE_MARKET):
        if side.lower() not in ["buy", "sell"]:
            raise ValueError("Trade side must be 'buy' or 'sell'.")

        order_side = SIDE_BUY if side.lower() == "buy" else SIDE_SELL

        # Execute the trade
        order = self.client.futures_create_order(
            symbol=symbol,
            side=order_side,
            type=order_type,
            quantity=quantity
        )
        return order

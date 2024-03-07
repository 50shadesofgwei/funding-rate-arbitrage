from binance.enums import *

def get_order_from_opportunity(opportunity, is_long: bool):
        side = SIDE_BUY if is_long else SIDE_SELL
        order_without_amount = {
            'symbol': opportunity['symbol'] + 'USDT',
            'side': side,
            'type': ORDER_TYPE_MARKET,
            'quantity': 0.0
        }
        return order_without_amount

def add_amount_to_order(order_without_amount, amount: float):
    order_with_amount = order_without_amount.copy()
    order_with_amount['quantity'] = amount
    return order_with_amount
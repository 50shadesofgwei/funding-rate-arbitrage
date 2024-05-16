from binance.enums import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

ALL_MARKETS = [
    'ETHUSDT',
    'BTCUSDT'
]

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
    order_with_amount['quantity'] = abs(round(amount, 3))
    return order_with_amount

def parse_trade_data_from_response(response) -> dict:
    trade_data = {
        "exchange": "Binance",
        "symbol": response['symbol'],
        "side": response['side'],
        "size": response['executedQty'],
        "liquidation_price": response['liquidationPrice']
    }

    return trade_data

def calculate_adjusted_trade_size(opportunity, is_long: bool, trade_size: float) -> float:
        try:
            leverage_factor = float(os.getenv('TRADE_LEVERAGE'))
            trade_size_in_asset = get_asset_amount_for_given_dollar_amount(opportunity['symbol'], trade_size)
            trade_size_with_leverage = trade_size_in_asset * leverage_factor
            adjusted_trade_size_raw = adjust_trade_size_for_direction(trade_size_with_leverage, is_long)
            adjusted_trade_size = round(adjusted_trade_size_raw, 3)
            logger.info(f'BinancePositionController - levered trade size in asset calculated at {adjusted_trade_size}')
            return adjusted_trade_size
        except Exception as e:
            logger.error(f"BinancePositionController - Failed to calculate adjusted trade size. Error: {e}")
            return None

def get_side(side: str) -> str:
    if side == "SELL":
        return "Short"
    elif side == "BUY":
        return "Long"
    else:
        logger.error(f"BinancePositionControllerUtils - get_side given invalid argument: {side}")
        return 
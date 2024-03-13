import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from pubsub import pub
from decimal import Decimal
from PositionMonitor.Synthetix.utils import *

class SynthetixPositionMonitor():
    def __init__(self):
        self.client = get_synthetix_client()

    def get_position_object_from_event(self, order_confirmation_object) -> dict:
        symbol = order_confirmation_object['position']['symbol']
        full_asset_name = get_full_asset_name(symbol=symbol)
        current_asset_price = get_asset_price(full_asset_name)
        side = get_side(order_confirmation_object['position']['position_size'])
        size_in_asset = order_confirmation_object['position']['position_size']
        size_in_dollars = get_dollar_amount_for_given_asset_amount(symbol, size_in_asset)
        liquidation_price = calculate_liquidation_price(order_confirmation_object['position']['symbol'], current_asset_price)

        return {
            'exchange': 'Synthetix',
            'symbol': symbol,
            'side': side,
            'size': size_in_dollars,
            'order_id': 0,
            'liquidation_price': liquidation_price
        }

    

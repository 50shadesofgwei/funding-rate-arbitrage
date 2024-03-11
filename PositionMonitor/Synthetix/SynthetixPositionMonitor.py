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

    def get_position_object_from_event(self, position):
        symbol = position['symbol']
        liquidation_price = calculate_liquidation_price(position["symbol"])

        return {
            'exchange': 'Synthetix',
            'symbol': symbol,
            'side': side,
            'order_id': order_id,
            'liquidation_price': liquidation_price
        }

    

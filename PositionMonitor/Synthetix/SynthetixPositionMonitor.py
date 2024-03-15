import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from synthetix import *
from APICaller.Synthetix.SynthetixUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from pubsub import pub
from decimal import Decimal
from PositionMonitor.Synthetix.utils import *
import uuid

class SynthetixPositionMonitor():
    def __init__(self):
        self.client = get_synthetix_client()


    

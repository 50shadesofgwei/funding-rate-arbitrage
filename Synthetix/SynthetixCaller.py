from synthetix import *
from SynthetixUtils import *

class SynthetixCaller:
    def __init__(self):
        self.client = get_synthetix_client()
        

    def get_funding_rate(self):
        markets = self.client.perps.get_markets()

        print(markets)


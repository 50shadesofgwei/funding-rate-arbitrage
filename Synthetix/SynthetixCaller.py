from synthetix import *
from SynthetixUtils import *

class SynthetixCaller:
    def __init__(self):
        hub = SynthetixClientHub()
        self.clients = SynthetixClients(hub)

    @staticmethod
    def get_funding_rate(client: Synthetix):
        test = client.perps.get_markets()
        print(test)
    
caller_instance = SynthetixCaller()
caller_instance.get_funding_rate(caller_instance.clients.optimism)


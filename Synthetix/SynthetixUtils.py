from synthetix import *
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

class SynthetixEnvVars(Enum):
    MAINNET_PROVIDER_RPC = 'MAINNET_PROVIDER_RPC'
    CHAIN_ID_MAINNET = 'CHAIN_ID_MAINNET'
    OPTIMISM_PROVIDER_RPC = 'OPTIMISM_PROVIDER_RPC'
    CHAIN_ID_OPTIMISM = 'CHAIN_ID_OPTIMISM'
    BASE_PROVIDER_RPC = 'BASE_PROVIDER_RPC'
    CHAIN_ID_BASE = 'CHAIN_ID_BASE'
    ADDRESS = 'ADDRESS'
    PRIVATE_KEY = 'PRIVATE_KEY'

    
    def get_value(self):
        value = os.getenv(self.value)
        if value is None:
            raise ValueError(f"Environment variable for {self.name} not found.")
        return value

class SynthetixClientHub:
    def __init__(self):
        self.clients = {
            'mainnet': Synthetix(
                provider_rpc=SynthetixEnvVars.MAINNET_PROVIDER_RPC.get_value(),
                network_id=SynthetixEnvVars.CHAIN_ID_MAINNET.get_value(),
                address=SynthetixEnvVars.ADDRESS.get_value(),
                private_key=SynthetixEnvVars.PRIVATE_KEY.get_value()
            ),
            'optimism': Synthetix(
                provider_rpc=SynthetixEnvVars.OPTIMISM_PROVIDER_RPC.get_value(),
                network_id=SynthetixEnvVars.CHAIN_ID_OPTIMISM.get_value(),
                address=SynthetixEnvVars.ADDRESS.get_value(),
                private_key=SynthetixEnvVars.PRIVATE_KEY.get_value()
            ),
            'base': Synthetix(
                provider_rpc=SynthetixEnvVars.BASE_PROVIDER_RPC.get_value(),
                network_id=SynthetixEnvVars.CHAIN_ID_BASE.get_value(),
                address=SynthetixEnvVars.ADDRESS.get_value(),
                private_key=SynthetixEnvVars.PRIVATE_KEY.get_value()
            )
        }

    def get_client(self, chain_name):
        return self.clients.get(chain_name)


class SynthetixClients:
    hub = SynthetixClientHub

    def __init__(self, hub: SynthetixClientHub):
        self.mainnet = hub.get_client('mainnet')
        self.optimism = hub.get_client('optimism')
        # self.base = hub.get_client('base')



from synthetix import *
import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

class SynthetixEnvVars(Enum):
    BASE_PROVIDER_RPC = 'BASE_PROVIDER_RPC'
    CHAIN_ID_BASE = 'CHAIN_ID_BASE'
    ADDRESS = 'ADDRESS'
    PRIVATE_KEY = 'PRIVATE_KEY'

    
    def get_value(self):
        value = os.getenv(self.value)
        if value is None:
            raise ValueError(f"Environment variable for {self.name} not found.")
        return value


def get_synthetix_client() -> Synthetix:
    synthetix_client = Synthetix(
                provider_rpc=SynthetixEnvVars.BASE_PROVIDER_RPC.get_value(),
                network_id=SynthetixEnvVars.CHAIN_ID_BASE.get_value(),
                address=SynthetixEnvVars.ADDRESS.get_value(),
                private_key=SynthetixEnvVars.PRIVATE_KEY.get_value()
    )
    return synthetix_client



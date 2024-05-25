from hmx2.hmx_client import Client as HMX
import os

def get_HMX_client() -> HMX:
    client = HMX(
        rpc_url=str(os.getenv('ARBITRUM_PROVIDER_RPC')),
        eth_private_key=str(os.getenv('PRIVATE_KEY'))
    )
    return client
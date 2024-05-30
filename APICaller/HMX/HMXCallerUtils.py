from hmx2.hmx_client import Client as HMX
import os

def get_HMX_client() -> HMX:
    client = HMX(
        rpc_url=str(os.getenv('ARBITRUM_PROVIDER_RPC')),
        eth_private_key=str(os.getenv('PRIVATE_KEY'))
    )
    return client

def calculate_daily_funding_velocity(skew_usd: float) -> float:
    base_skew = 250000
    velocity_increment = 0.1 

    increments = skew_usd / base_skew
    daily_funding_velocity = increments * velocity_increment

    return daily_funding_velocity
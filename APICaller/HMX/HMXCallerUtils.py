from hmx2.hmx_client import Client as HMX
from GlobalUtils.logger import logger
import os

def get_HMX_client() -> HMX:
    client = HMX(
        rpc_url=str(os.getenv('ARBITRUM_PROVIDER_RPC')),
        eth_private_key=str(os.getenv('PRIVATE_KEY'))
    )
    return client

def calculate_daily_funding_velocity(symbol: str, skew_usd: float) -> float:
    max_funding_rate = (8 / 365)
    skew_scale = get_skew_scale_for_token(symbol)
    daily_funding_velocity = (max_funding_rate / skew_scale) * skew_usd

    return daily_funding_velocity

def get_skew_scale_for_token(symbol: str) -> int:
    try:
        skew_scale_mapping_usd = {
            'BTC': 3000000000,
            'ETH': 2000000000,
            'ARB': 200000000,
            'AVAX': 200000000,
            'BNB': 200000000,
            'DOGE': 300000000,
            'ENA': 200000000,
            'LINK': 200000000,
            'OP': 200000000,
            'PENDLE': 200000000,
            'PYTH': 50000000,
            'SOL': 200000000,
            'XRP': 500000000
        }
        result = skew_scale_mapping_usd.get(symbol)
        if result is None:
            logger.warning(f'HMXCallerUtils - Skew scale for symbol {symbol} not found in mapping.')
        return result
    
    except Exception as e:
        logger.error(f'HMXCallerUtils - Failed to retrieve skew scale for symbol {symbol} from mapping. Error: {e}')
        return None

GLOBAL_HMX_CLIENT = get_HMX_client()
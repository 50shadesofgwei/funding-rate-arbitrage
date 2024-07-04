from GlobalUtils.logger import *


def get_params_object_from_opportunity_dict(opportunity: dict, is_long: bool, trade_size: float) -> dict:
    try:
        symbol = opportunity['symbol']
        parameters = {
            "chain": 'arbitrum',
            "index_token_symbol": symbol,
            "collateral_token_symbol": symbol,
            "start_token_symbol": "USDC",
            "is_long": is_long,
            "size_delta_usd": trade_size,
            "leverage": 1,
            "slippage_percent": 0.003
        }
        return parameters
    
    except Exception as e:
        logger.error(f'GMXPositionControllerUtils - Failed to build a parameters object from opportunity. Error: {e}')
        return None
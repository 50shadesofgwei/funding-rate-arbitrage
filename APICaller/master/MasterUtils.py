from GlobalUtils.logger import logger

TARGET_TOKENS = [
    {"token": "BTC", "is_target": True},
    {"token": "ETH", "is_target": True},
    {"token": "SNX", "is_target": False},
    {"token": "SOL", "is_target": True},
    {"token": "W", "is_target": False},
    {"token": "WIF", "is_target": False},
    {"token": "ARB", "is_target": False},
    {"token": "BNB", "is_target": False},
    {"token": "ENA", "is_target": False},
    {"token": "DOGE", "is_target": True},
    {"token": "AVAX", "is_target": False},
    {"token": "PENDLE", "is_target": False},

]

TARGET_EXCHANGES = [
    {"exchange": "Synthetix", "is_target": True},
    {"exchange": "Binance", "is_target": False},
    {"exchange": "ByBit", "is_target": False},
    {"exchange": "HMX", "is_target": False},
    {"exchange": "GMX", "is_target": True},
]

def get_target_exchanges() -> list:
    try:
        exchanges = [exchange["exchange"] for exchange in TARGET_EXCHANGES if exchange["is_target"]]
        return exchanges
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target exchanges: {e}")
        return []

def get_all_target_token_lists() -> list:
    try:
        binance_token_list = get_target_tokens_for_binance()
        synthetix_token_list = get_target_tokens_for_synthetix()
        bybit_token_list = get_target_tokens_for_bybit()
        hmx_token_list = get_target_tokens_for_HMX()
        gmx_token_list = get_target_tokens_for_GMX()
        all_target_token_lists = [
            synthetix_token_list,
            binance_token_list,
            bybit_token_list,
            hmx_token_list,
            gmx_token_list
        ]
        return all_target_token_lists
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving all target token lists: {e}")
        return []

def get_target_tokens_for_binance() -> list:
    try:
        symbols = [token["token"] + "USDT" for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for Binance: {e}")
        return []

def get_target_tokens_for_synthetix() -> list:
    try:
        symbols = [token["token"] for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for Synthetix: {e}")
        return []

def get_target_tokens_for_bybit() -> list:
    try:
        symbols = [token["token"] + "USDT" for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for ByBit: {e}")
        return []

def get_target_tokens_for_HMX() -> list:
    try:
        symbols = [token["token"] + "USD" for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for ByBit: {e}")
        return []

def get_target_tokens_for_synthetix() -> list:
    try:
        symbols = [token["token"] for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for Synthetix: {e}")
        return []

def get_target_tokens_for_GMX() -> list:
    try:
        symbols = [token["token"] for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for GMX: {e}")
        return []
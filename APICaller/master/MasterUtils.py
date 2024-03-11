from GlobalUtils.logger import logger

TARGET_TOKENS = [
    {"token": "BTC", "is_target": True},
    {"token": "ETH", "is_target": True},
]

TARGET_EXCHANGES = [
    {"exchange": "Synthetix", "is_target": True},
    {"exchange": "Binance", "is_target": False},
    {"exchange": "ByBit", "is_target": True},
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
        bybit_token_list = get_target_tokens_for_bybit()
        synthetix_token_list = get_target_tokens_for_synthetix()
        all_target_token_lists = [
            synthetix_token_list,
            binance_token_list,
            bybit_token_list,
        ]
        return all_target_token_lists
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving all target token lists: {e}")
        return []


def get_target_tokens_for_bybit() -> list:
    try:
        symbols = [token["token"] + "PERP" for token in TARGET_TOKENS if token["is_target"]]
        return symbols
    except Exception as e:
        logger.error(f"MasterAPICallerUtils - Error retrieving target tokens for Bybit: {e}")
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

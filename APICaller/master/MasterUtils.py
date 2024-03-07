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
    exchanges = [exchange["exchange"] for exchange in TARGET_EXCHANGES if exchange["is_target"]]
    return exchanges

def get_all_target_token_lists() -> list:
    binance_token_list = get_target_tokens_for_binance()
    bybit_token_list = get_target_tokens_for_bybit()
    synthetix_token_list = get_target_tokens_for_synthetix()
    all_target_token_lists = [
        synthetix_token_list,
        binance_token_list,
        bybit_token_list,
        
    ]
    return all_target_token_lists

def get_target_tokens_for_bybit() -> list:
    symbols = [token["token"] + "PERP" for token in TARGET_TOKENS if token["is_target"]]
    return symbols

def get_target_tokens_for_binance() -> list:
    symbols = [token["token"] + "USDT" for token in TARGET_TOKENS if token["is_target"]]
    return symbols

def get_target_tokens_for_synthetix() -> list:
    symbols = [token["token"] for token in TARGET_TOKENS if token["is_target"]]
    return symbols
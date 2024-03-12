from PositionMonitor.Synthetix.utils import *
from GlobalUtils.globalUtils import *
import re

def parse_trade_data_from_position_details(position_details) -> dict:
    side = get_side(position_details['position']['size'])
    full_asset_name = get_full_asset_name(position_details['position']['symbol'])
    asset_price = get_asset_price(full_asset_name)
    liquidation_price = calculate_liquidation_price(position_details, asset_price)

    trade_data = {
        "exchange": "Synthetix",
        "symbol": position_details['position']['symbol'],
        "side": side,
        "size": position_details['position']['size'],
        "liquidation_price": liquidation_price
        }

    return trade_data

def is_transaction_hash(tx_hash) -> bool:
    # Regular expression to match an Ethereum transaction hash
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return re.match(pattern, tx_hash) is not None
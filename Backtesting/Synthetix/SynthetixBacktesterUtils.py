from enum import Enum
import json
import os
from GlobalUtils.logger import *
from web3 import Web3

from dotenv import load_dotenv

load_dotenv()

provider_url = os.getenv('BASE_PROVIDER_RPC')
client = Web3(Web3.HTTPProvider(provider_url))

class ContractAddresses(Enum):
    PERPS = Web3.to_checksum_address('0x0a2af931effd34b81ebcc57e3d3c9b1e1de1c9ce')

def get_perps_contract():
    try:
        with open(json_filepath, 'r') as file:
            abi = json.load(file)
            json_filepath = 'Backtesting/Synthetix/perps_contract_abi.json'
    except FileNotFoundError:
        logger.error(f"SynthetixBacktesterUtils - Contract ABI file does not exist at filepath: {json_filepath}")
        raise
    except json.JSONDecodeError:
        logger.error("SynthetixBacktesterUtils - ABI file is not valid JSON")
        raise
    return client.eth.contract(address=ContractAddresses.PERPS.value, abi=abi)

def get_event_logs(num_blocks: int):
    try:
        contract = get_perps_contract()
        latest_block = client.eth.block_number
        from_block = max(latest_block - num_blocks, 0)
        event_filter = contract.events.MarketUpdated.create_filter(fromBlock=from_block, toBlock='latest')
        events = event_filter.get_all_entries()
        return events
    except Exception as e:
        logger.error(f"SynthetixBacktesterUtils - Error interacting with contract: {e}")


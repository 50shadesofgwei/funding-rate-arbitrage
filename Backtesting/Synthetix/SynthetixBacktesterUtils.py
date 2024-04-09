from enum import Enum
import json
import os
import logging
from web3 import Web3

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ContractAddresses(Enum):
    PERPS = Web3.to_checksum_address('0x0a2af931effd34b81ebcc57e3d3c9b1e1de1c9ce')

provider_url = os.getenv('BASE_PROVIDER_RPC')
print("Provider URL:", provider_url)
client = Web3(Web3.HTTPProvider(provider_url))

if not client.is_connected():
    logger.error("Failed to connect to Ethereum provider at: {}".format(provider_url))
    raise Exception("Connection to Ethereum provider failed")

json_filepath = 'Backtesting/Synthetix/perps_contract_abi.json'
try:
    with open(json_filepath, 'r') as file:
        abi = json.load(file)
except FileNotFoundError:
    logger.error(f"Contract ABI file does not exist at filepath: {json_filepath}")
    raise
except json.JSONDecodeError:
    logger.error("ABI file is not valid JSON")
    raise

def get_perps_contract():
    """ Returns a Web3 contract instance for the specified Perpetual Contracts. """
    return client.eth.contract(address=ContractAddresses.PERPS.value, abi=abi)

def main():
    try:
        contract = get_perps_contract()
        latest_block = client.eth.block_number
        from_block = max(latest_block - 10000, 0)
        event_filter = contract.events.MarketUpdated.create_filter(fromBlock=from_block, toBlock='latest')
        events = event_filter.get_all_entries()
        print("Events:", events)
    except Exception as e:
        logger.error(f"Error interacting with contract: {e}")

if __name__ == "__main__":
    main()


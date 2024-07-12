from GlobalUtils.logger import logger
import json
from GlobalUtils.globalUtils import *
from gmx_python_sdk.scripts.v2.get.get import GetData
from gmx_python_sdk.scripts.v2.gmx_utils import *
from APICaller.GMX.GMXCallerUtils import ARBITRUM_CONFIG_OBJECT

class GMXMarketDirectory:
    _markets = {}
    _file_path = 'gmx_markets.json'
    _is_initialized = False
    _symbol_to_market_id_mapping = {}
    _data_getter = GetData(config=ARBITRUM_CONFIG_OBJECT)

    @classmethod
    def initialize(cls):
        try:
            if not cls._is_initialized:
                cls.update_all_market_parameters()
                cls._is_initialized = True
                logger.info('GMXMarketDirectory - Markets Initialized')
                with open(cls._file_path, 'r') as file:
                    cls._markets = json.load(file)
        except FileNotFoundError:
            logger.error("GMXMarketDirectory - No existing market file found. Starting fresh.")
        except json.JSONDecodeError:
            logger.error("GMXMarketDirectory - Error decoding JSON. Starting with an empty dictionary.")

    @classmethod
    def save_market_to_file(cls):
        try:
            with open(cls._file_path, 'w') as file:
                json.dump(cls._markets, file)
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to save markets to file: {e}")
    
    @classmethod
    def load_markets_from_file(cls):
        try:
            with open('markets.json', 'r') as f:
                cls._markets = json.load(f)
        except FileNotFoundError:
            logger.error("MarketDirectory - Market file not found. Starting with an empty dictionary.")
            cls._markets = {}
    
    @classmethod
    @deco_retry
    def update_all_market_parameters(cls):
        try:
            mapper = []
            output_list = []

            for market_key in cls._data_getter.markets.info:
                symbol = cls._data_getter.markets.get_market_symbol(market_key)
                index_token_address = cls._data_getter.markets.get_index_token_address(
                    market_key
                )
                if index_token_address == NULL_ADDRESS:
                    continue

                cls._data_getter._get_token_addresses(market_key)

                output = cls._data_getter._get_oracle_prices(
                market_key,
                index_token_address,
            )

                mapper.append(symbol)
                output_list.append(output)

            # Multithreaded call on contract
            threaded_output = execute_threading(output_list)
            for (
                output,
                symbol
            ) in zip(
                threaded_output,
                mapper
            ):

                print(output[5])
                market_info_dict = {
                    "market_token": output[0][0],
                    "index_token": output[0][1],
                    "long_token": output[0][2],
                    "short_token": output[0][3],
                    "is_long_pays_short": output[4][0],
                    "funding_factor_per_second": output[4][1]
                }

        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to fetch market parameters. Error: {e}", exc_info=True)
            return None

    @classmethod
    def update_market_member(cls, market_data):
        symbol = market_data['market_name']

        cls._markets[symbol] = {
            'symbol': symbol,
            'market_id': market_data['market_id'],
            'max_funding_velocity': market_data['max_funding_velocity'],
            'skew_scale': market_data['skew_scale'],
            'maker_fee': market_data['maker_fee'],
            'taker_fee': market_data['taker_fee']
        }
    
    @classmethod
    def build_symbol_to_market_id_mapping(cls) -> dict:
        try:
            mapping = {}

            for market_key in cls._data_getter.markets.info:
                symbol = cls._data_getter.markets.get_market_symbol(market_key)
                mapping[symbol] = market_key
            
            return mapping
        
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to build symbol/marketId mapping. Error: {e}")
            return None
    
    @classmethod
    def get_market_key_for_symbol(cls, symbol: str) -> str:
        try:
            market_key = str(cls._symbol_to_market_id_mapping[symbol])
            return market_key
        
        except KeyError as ke:
            logger.error(f"GMXMarketDirectory - KeyError while calling market key for symbol {symbol}. Error: {ke}")
            return None
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Error while calling market key for symbol {symbol}. Error: {e}")
            return None


# data_getter = GetData(config=ARBITRUM_CONFIG_OBJECT)
# x = data_getter.markets.info
# print(x)

from GlobalUtils.logger import logger
import json
from GlobalUtils.globalUtils import *
from gmx_python_sdk.scripts.v2.get.get import GetData
from gmx_python_sdk.scripts.v2.gmx_utils import *
from APICaller.GMX.GMXCallerUtils import ARBITRUM_CONFIG_OBJECT
from APICaller.GMX.GMXContractUtils import *

class GMXMarketDirectory:
    _markets = {}
    _file_path = 'GMXmarkets.json'
    _is_initialized = False
    _symbol_to_market_key_mapping = {}
    _data_getter = GetData(config=ARBITRUM_CONFIG_OBJECT)

    @classmethod
    def initialize(cls):
        try:
            if not cls._is_initialized:
                cls._symbol_to_market_key_mapping = cls.build_symbol_to_market_id_mapping()
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
            with open('GMXmarkets.json', 'r') as f:
                cls._markets = json.load(f)
        except FileNotFoundError:
            logger.error("MarketDirectory - Market file not found. Starting with an empty dictionary.")
            cls._markets = {}
    
    @classmethod
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

                market_key = cls._symbol_to_market_key_mapping[symbol]
                min_collateral_factor = get_min_collateral_factor(market_key)
                funding_exponent = get_funding_exponent(market_key)
                funding_factor = get_funding_factor(market_key)
                funding_increase_factor = get_funding_increase_factor(market_key)
                funding_decrease_factor = get_funding_decrease_factor(market_key)
                threshold_for_stable_funding = get_threshold_for_decrease_funding(market_key)
                threshold_for_decrease_funding = get_threshold_for_decrease_funding(market_key)
                
                market_info_dict = {
                    "market": symbol,
                    "market_key": market_key,
                    "maker_fee_percent": 0.05,
                    "taker_fee_percent": 0.07,
                    "min_collateral_factor": min_collateral_factor,
                    "funding_exponent": funding_exponent,
                    "funding_factor": funding_factor,
                    "funding_increase_factor": funding_increase_factor,
                    "funding_decrease_factor": funding_decrease_factor,
                    "threshold_for_stable_funding": threshold_for_stable_funding,
                    "threshold_for_decrease_funding": threshold_for_decrease_funding
                }

                cls._markets[symbol] = market_info_dict
            
            cls.save_market_to_file()
            return
            
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to fetch market parameters. Error: {e}", exc_info=True)
            return None
    
    @classmethod
    def calculate_new_funding_velocity(cls, symbol: str, absolute_trade_size_usd: float, is_long: bool) -> float:
        try:
            market = cls.get_market_key_for_symbol(symbol)
            threshold_for_decrease_funding = get_threshold_for_decrease_funding(market)
            threshold_for_stable_funding = get_threshold_for_stable_funding(market)
            funding_increase_factor = get_funding_increase_factor(market)
            open_interest = OpenInterest(ARBITRUM_CONFIG_OBJECT)._get_data_processing(market)
            long_open_interest = open_interest['long'][symbol]
            short_open_interest = open_interest['short'][symbol]

            if is_long:
                long_open_interest += absolute_trade_size_usd
            else:
                short_open_interest += absolute_trade_size_usd

            is_long_side_heavier: bool = long_open_interest > short_open_interest

            if is_long_side_heavier:
                imbalance = (long_open_interest / short_open_interest) - 1
            else:
                imbalance = (short_open_interest / long_open_interest) - 1
    

            if is_long_side_heavier and imbalance > threshold_for_stable_funding:
                print(f'condition 1: funding_increase_factor = {funding_increase_factor}, imbalance = {imbalance}')
                funding_velocity_24h = funding_increase_factor * imbalance * 86400 
            if not is_long_side_heavier and imbalance > threshold_for_decrease_funding:
                print(f'condition 2: funding_increase_factor = {funding_increase_factor}, imbalance = {imbalance}')
                funding_velocity_24h = funding_increase_factor * imbalance * 86400
            if is_long_side_heavier and imbalance < threshold_for_stable_funding:
                funding_velocity_24h = 0
            if not is_long_side_heavier and imbalance < threshold_for_decrease_funding:
                funding_velocity_24h = 0

            return funding_velocity_24h
                
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to calculate new funding velocity for symbol {symbol}. Error: {e}", exc_info=True)
            return None

    @classmethod
    def get_open_interest_imbalance_percentage(cls, market: str) -> float:
        try:
            symbol = cls.get_symbol_for_market_key(market)
            open_interest = OpenInterest(ARBITRUM_CONFIG_OBJECT)._get_data_processing(market)
            long_open_interest = open_interest['long'][symbol]
            short_open_interest = open_interest['short'][symbol]
            imbalance = (long_open_interest / short_open_interest) - 1
            imbalance_percentage = imbalance * 100

            return imbalance_percentage
        
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to fetch open interest imbalance. Error: {e}", exc_info=True)
            return None

    @classmethod
    def get_market_params(cls, symbol: str) -> dict:
        try:
            for key, value in cls._markets.items():
                    if key == symbol:
                        return value
            return None
        
        except KeyError as ke:
            logger.error(f"GMXMarketDirectory - KeyError while getting market params for {symbol} Error: {ke}")
            return None
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to get market parameters for symbol from local storage. Error: {e}", exc_info=True)
            return None

    
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
            market_key = str(cls._symbol_to_market_key_mapping[symbol])
            return market_key
        
        except KeyError as ke:
            logger.error(f"GMXMarketDirectory - KeyError while calling market key for symbol {symbol}. Error: {ke}")
            return None
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Error while calling market key for symbol {symbol}. Error: {e}")
            return None
    
    @classmethod
    def get_symbol_for_market_key(cls, market_key: str) -> str:
        try:
            for key, value in cls._symbol_to_market_key_mapping.items():
                if value == market_key:
                    return key
            return None

        except Exception as e:
            logger.error(f"GMXMarketDirectory - Error while getting symbol for market key {market_key}. Error: {e}")
            return None        

    @classmethod
    def get_total_opening_fee(cls, symbol: str, skew_usd: float, is_long: bool, absolute_size_usd: float) -> float:
        try:
            fees = cls.get_maker_taker_fee(
                symbol,
                skew_usd,
                is_long,
                absolute_size_usd
            )
        
            maker_fee_usd = fees[0]['maker_fee'] * fees[0]['size']
            taker_fee_usd = fees[1]['taker_fee'] * fees[1]['size']

            total_opening_fee_usd = maker_fee_usd + taker_fee_usd
            return total_opening_fee_usd

        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to determine total opening fee for {symbol} with skew {skew_usd}, size {absolute_size_usd} and is_long = {is_long}. Error: {e}")
            return None
    
    @classmethod
    def get_total_closing_fee(cls, symbol: str, skew_usd_after_trade: float, is_long: bool, absolute_size_usd: float) -> float:
        try:
            fees = cls.get_maker_taker_fee(
                symbol,
                skew_usd_after_trade,
                is_long,
                -absolute_size_usd
            )
        
            maker_fee_usd = fees[0]['maker_fee'] * fees[0]['size']
            taker_fee_usd = fees[1]['taker_fee'] * fees[1]['size']

            total_opening_fee_usd = maker_fee_usd + taker_fee_usd
            return total_opening_fee_usd

        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to determine total opening fee for {symbol} with skew {skew_usd_after_trade}, size {absolute_size_usd} and is_long = {is_long}. Error: {e}")
            return None

    @classmethod
    def get_maker_taker_fee(cls, symbol: str, skew_usd: float, is_long: bool, absolute_size_usd: float) -> list:
        try:
            market = cls.get_market_params(symbol)
            maker_fee = market['maker_fee_percent']
            taker_fee = market['taker_fee_percent']

            if is_long:
                trade_impact = absolute_size_usd
            else:
                trade_impact = -absolute_size_usd

            maker_taker_split = cls.calculate_maker_taker_split(skew_usd, trade_impact)
            maker_size = maker_taker_split['maker_trade_size']
            taker_size = maker_taker_split['taker_trade_size']


            fees = [
                {'maker_fee': maker_fee, 'size': maker_size},
                {'taker_fee': taker_fee, 'size': taker_size}
            ]

            return fees

        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to determine maker/taker fee object for {symbol} with skew {skew_usd}, size {absolute_size_usd} and is_long = {is_long}. Error: {e}")
            return None

    @classmethod        
    def calculate_maker_taker_split(cls, skew_usd: float, size_usd: float) -> dict:
        try:
            maker_trade_size = 0
            taker_trade_size = 0

            if (skew_usd > 0 and size_usd < 0) or (skew_usd < 0 and size_usd > 0):
                # Trade is neutralizing the skew
                if abs(size_usd) >= abs(skew_usd):
                    maker_trade_size = abs(skew_usd)
                    taker_trade_size = abs(size_usd) - abs(skew_usd)
                else:
                    maker_trade_size = abs(size_usd)
            else:
                # Trade is increasing the skew
                taker_trade_size = abs(size_usd)

            return {
                'maker_trade_size': maker_trade_size,
                'taker_trade_size': taker_trade_size
            }
        
        except Exception as e:
            logger.error(f"GMXMarketDirectory - Failed to determine maker/taker split for skew {skew_usd} and size {size_usd}. Error: {e}")
            return None

GMXMarketDirectory.initialize()
x = GMXMarketDirectory.calculate_new_funding_velocity(
    'ETH',
    2000000,
    True
)
print(f'new funding velocity = {x}')
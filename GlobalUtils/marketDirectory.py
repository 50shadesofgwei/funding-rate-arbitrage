from web3 import *
from dotenv import load_dotenv
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
import json

load_dotenv()

class MarketDirectory:
    _markets = {}
    _file_path = 'markets.json'
    _is_initialized = False

    @classmethod
    def initialize(cls):
        try:
            if not cls._is_initialized:
                cls.update_all_market_parameters()
                cls._is_initialized = True
                logger.info('MarketDirectory - Markets Initialized')
                with open(cls._file_path, 'r') as file:
                    cls._markets = json.load(file)
        except FileNotFoundError:
            logger.error("MarketDirectory - No existing market file found. Starting fresh.")
        except json.JSONDecodeError:
            logger.error("MarketDirectory - Error decoding JSON. Starting with an empty dictionary.")

    @classmethod
    def save_market_to_file(cls):
        try:
            with open(cls._file_path, 'w') as file:
                json.dump(cls._markets, file)
        except Exception as e:
            logger.error(f"MarketDirectory - Failed to save markets to file: {e}")

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
        client = GLOBAL_SYNTHETIX_CLIENT
        market_data_response = client.perps.markets_by_name
        for symbol, market_data in market_data_response.items():
            cls.update_market_member(market_data)
            cls.save_market_to_file()

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
    def get_market_params(cls, symbol: str) -> dict:
        try:
            market: dict = cls._markets.get(symbol)
            if market:
                return market
            else:
                logger.error(f"MarketDirectory - No data available for market {symbol}.")
                return None
        
        except Exception as e:
            logger.error(f"MarketDirectory - Error while getting market params for {symbol}. market = {market}. Error: {e}")
            return None

    @classmethod
    def get_market_id(cls, symbol: str) -> int:
        try:
            market = cls._markets.get(symbol)
            if market:
                return market['market_id']
            logger.error(f"MarketDirectory - Market symbol '{symbol}' not found in MarketDirectory.")

        except Exception as e:
            logger.error(f'Failed to get market id for symbol: {symbol}, market = {market}. Error: {e}')
            return None


    @classmethod
    def calculate_new_funding_velocity(cls, symbol: str, current_skew: float, trade_size: float) -> float:
        try:
            market_data = cls.get_market_params(symbol)
            c = market_data['max_funding_velocity'] / market_data['skew_scale']
            new_skew = current_skew + trade_size
            new_funding_velocity = c * new_skew
            return new_funding_velocity
        except Exception as e:
            logger.error(f"MarketDirectory - Failed to calculate new funding velocity for {symbol}: {e}")

    @classmethod
    def get_total_opening_fee(cls, symbol: str, skew_usd: float, is_long: bool, size_usd: float) -> float:
        try:
            fees = cls.get_maker_taker_fee(
                symbol,
                skew_usd,
                is_long,
                size_usd
            )
        
            maker_fee_usd = fees[0]['maker_fee'] * fees[0]['size']
            taker_fee_usd = fees[1]['taker_fee'] * fees[1]['size']

            total_opening_fee_usd = maker_fee_usd + taker_fee_usd
            return total_opening_fee_usd

        except Exception as e:
            logger.error(f"MarketDirectory - Failed to determine total opening fee for {symbol} with skew {skew_usd}, size {size_usd} and is_long = {is_long}. Error: {e}")
            return None

    @classmethod
    def get_maker_taker_fee(cls, symbol: str, skew_usd: float, is_long: bool, size_usd: float) -> list:
        try:
            market = cls.get_market_params(symbol)
            maker_fee = market['maker_fee']
            taker_fee = market['taker_fee']
            print(f'Maker fee for {symbol} = {maker_fee}')
            print(f'Taker fee for {symbol} = {taker_fee}')

            if is_long:
                trade_impact = size_usd
            else:
                trade_impact = -size_usd

            maker_taker_split = cls.calculate_maker_taker_split(skew_usd, trade_impact)
            maker_size = maker_taker_split['maker_trade_size']
            taker_size = maker_taker_split['taker_trade_size']


            fees = [
                {'maker_fee': maker_fee, 'size': maker_size},
                {'taker_fee': taker_fee, 'size': taker_size}
            ]

            return fees

        except Exception as e:
            logger.error(f"MarketDirectory - Failed to determine maker/taker fee object for {symbol} with skew {skew_usd}, size {size_usd} and is_long = {is_long}. Error: {e}")
            return None

    @classmethod        
    def calculate_maker_taker_split(cls, skew_usd: float, size_usd: float) -> dict:
        try:
            # Initialize maker and taker sizes
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
            logger.error(f"MarketDirectory - Failed to determine maker/taker split for skew {skew_usd} and size {size_usd}. Error: {e}")
            return None


# Opening fee tests
# TODO: Delete these later
MarketDirectory.initialize()
test1 = MarketDirectory.get_total_opening_fee(
    'DOGE',
    0,
    False,
    5000)
print(f'expected = 6, result = {test1}')

test2 = MarketDirectory.get_total_opening_fee(
    'ETH',
    140000,
    True,
    6000)
print(f'expected = 1, result = {test2}')

test3 = MarketDirectory.get_total_opening_fee(
    'BTC',
    63000,
    False,
    5500)
print(f'expected = 1, result = {test3}')
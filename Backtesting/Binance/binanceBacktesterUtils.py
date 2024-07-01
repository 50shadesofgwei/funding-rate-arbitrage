from GlobalUtils.logger import logger
import pandas as pd
import json

MARKET_DEPLOYMENT_TIMESTAMP = 1702522800

def calculate_open_interest_differential_usd(ratio: float, open_interest: float, price: float) -> float:
    try:
        total_parts = ratio + 1
        long_ratio = ratio / total_parts
        short_ratio = 1 / total_parts
        long_value = long_ratio * open_interest * price
        short_value = short_ratio * open_interest * price

        differential = abs(long_value - short_value)

        return differential
    except TypeError:
        logger.info("BinanceBacktesterUtils - Invalid input types: ratio, open_interest, and price must be numbers.")
    except Exception as e:
        logger.info(f"BinanceBacktesterUtils - An error occurred: {e}")
    return 0.0

def save_data_to_json(data, symbol: str):
    try:
        filename = f'Backtesting/MasterBacktester/historicalDataJSON/Binance/{symbol}Historical.json'
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        logger.error(f'BinanceBacktester - Error while logging historical data to JSON file: {e}')
        return None

def extract_funding_events(funding_data: pd.DataFrame, start_block: int, end_block: int):
    try:
        return funding_data[(funding_data['block_number'] >= start_block) & (funding_data['block_number'] <= end_block)]
    except Exception as e:
        logger.error(f'BinanceBacktesterUtils - Error while extracting funding events for funding data {funding_data}, {e}')
        return None

def calculate_total_funding_impact(funding_events: pd.DataFrame, position_size_in_asset: float):
    try:
        total_impact: float = 0
        for index, event in funding_events.iterrows():
            total_impact += event['funding_rate'] * position_size_in_asset
        return total_impact
    
    except Exception as e:
        logger.error(f'BinanceBacktesterUtils - Error while calculating total funding impact for funding event dataframe {funding_events}, {e}')
        return None

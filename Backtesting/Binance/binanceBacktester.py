from APICaller.Binance.binanceCaller import BinanceCaller
from Backtesting.utils.backtestingUtils import *
from Backtesting.Binance.binanceBacktesterUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
import math
import time 
import json

class BinanceBacktester:
    BOUND_CONST: float = 0.68 ## 2 std. devs

    def __init__(self):
        self.caller = BinanceCaller()

    def build_statistics_dict(self, symbol: str) -> dict:
        formatted_symbol = symbol + 'USDT'
        max_limit = 1000
        rates = self.caller.get_historical_funding_rate_for_symbol(formatted_symbol, max_limit)
        past_week_average = self._get_past_week_average_rate(rates)
        past_month_average = self._get_past_month_average_rate(rates)
        past_year_average = self._get_past_year_average_rate(rates)
        average_period_out_of_bounds = self._get_average_duration_above_mean(rates=rates, mean=past_year_average)
        active_out_of_bounds_streak = self._get_current_out_of_bounds_streak(past_year_average, rates)
        open_interest_differential_usd = self._get_open_interest_usd_with_differential(formatted_symbol)


        stats = {
            'symbol': symbol,
            'past_week_avg': past_week_average,
            'past_month_avg': past_month_average,
            'past_year_avg': past_year_average,
            'average_period_out_of_bounds': average_period_out_of_bounds,
            'active_out_of_bounds_streak': active_out_of_bounds_streak,
            'long_short_ratio': open_interest_differential_usd['ratio'],
            'open_interest_usd': open_interest_differential_usd['open_interest_usd'],
            'open_interest_differential_usd': open_interest_differential_usd['differential_usd'],

        }

        return stats
    
    def _get_past_week_average_rate(self, rates: list) -> float:
        average_rate = self._calculate_average_funding_rate_for_period(period_days=7, rates=rates)
        return average_rate

    def _get_past_month_average_rate(self, rates: list) -> float:
        average_rate = self._calculate_average_funding_rate_for_period(period_days=30, rates=rates)
        return average_rate

    def _get_past_year_average_rate(self, rates: list) -> float:
        average_rate = self._calculate_average_funding_rate_for_period(period_days=math.floor(1000/3), rates=rates)
        return average_rate

    def _calculate_average_funding_rate_for_period(self, period_days: int, rates: list) -> float:
        num_rates = min(period_days * 3, len(rates))
        rate_total: float = 0
        for i in range(num_rates):
            funding_rate = float(rates[i]['fundingRate'])
            rate_total += funding_rate

        mean_rate_for_period = rate_total / num_rates
        return mean_rate_for_period

    def _get_current_out_of_bounds_streak(self, mean: float, data: list) -> int:
            lower_bound = mean * (1 - self.BOUND_CONST)
            upper_bound = mean * (1 + self.BOUND_CONST)

            current_streak = 0

            for rate in reversed(data):
                funding_rate = float(rate['fundingRate'])
                if funding_rate < lower_bound or funding_rate > upper_bound:
                    current_streak += 1
                else:
                    break

            return current_streak

    def _get_average_duration_above_mean(self, rates: list, mean: float):
        lower_bound = mean * (1 - self.BOUND_CONST)
        upper_bound = mean * (1 + self.BOUND_CONST)

        out_of_bounds_durations = []
        current_duration = 0
        out_of_bounds = False

        for rate in rates:
            funding_rate = float(rate['fundingRate'])
            if funding_rate < lower_bound or funding_rate > upper_bound:
                if not out_of_bounds:
                    out_of_bounds = True 
                    current_duration = 1 
                else:
                    current_duration += 1 
            else:
                if out_of_bounds:
                    out_of_bounds_durations.append(current_duration)
                    out_of_bounds = False
                    current_duration = 0

        if out_of_bounds:
            out_of_bounds_durations.append(current_duration)

        if out_of_bounds_durations:
            average_duration = sum(out_of_bounds_durations) / len(out_of_bounds_durations)
        else:
            average_duration = 0 

        return average_duration

    def _get_open_interest_usd_with_differential(self, symbol):
        try:
            open_interest_info = self._get_open_interest(symbol)
            current_price = self.caller.get_price(symbol)
            open_interest_usd = float(open_interest_info['open_interest'] * current_price)
            differential_usd = calculate_open_interest_differential_usd(open_interest_info['ratio'], open_interest_info['open_interest'], current_price)
            if open_interest_info is None or current_price is None:
                raise ValueError("BinanceBacktester - Failed to fetch open interest or current price from API.")

            data = {
                'open_interest_usd': open_interest_usd,
                'differential_usd': differential_usd,
                'ratio': open_interest_info['ratio']
            }
            return data
        except Exception as e:
            logger.info(f"BinanceBacktester - Error calculating dollar value of open interest for {symbol}: {e}")
            return None

    def _get_open_interest(self, symbol: str):
        try:
            response = self.caller.client.open_interest(symbol)
            ratio_response = self.caller.client.taker_long_short_ratio(symbol, period='6h', limit=3)
            ratio = float(ratio_response[0]['buySellRatio'])
            open_interest = float(response['openInterest'])

            data = {
                'open_interest': open_interest,
                'ratio': ratio
            }
            
            if 'openInterest' not in response:
                raise KeyError("BinanceBacktester - openInterest key not found in API response.")

            if 'buySellRatio' not in ratio_response[0]:
                raise KeyError("BinanceBacktester - buySellRatio key not found in API response.")
            
            return data
        except KeyError as e:
            logger.info(f"BinanceBacktester - Missing data in response: {e}")
            return None
        except Exception as e:
            logger.info(f"Failed to fetch open interest for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str):
        """Fetches historical funding rate data for a symbol from the Binance API and writes it to a JSON file"""
        try:
            data = self.build_backtest_data(symbol)
            save_data_to_json(data, symbol)
            return
        except Exception as e:
            logger.error(f'BinanceBacktester - Error while fetching historical data for JSON file: {e}')
            return

    def load_data_from_json(self, symbol: str):
        try:
            filename = f'Backtesting/MasterBacktester/historicalDataJSON/Binance/{symbol}Historical.json'
            with open(filename, 'r') as file:
                data = json.load(file)
            if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
                raise ValueError("BinanceBacktester - Loaded data is not a list of dictionaries.")
            return data
        except Exception as e:
            logger.error(f'BinanceBacktester - Error while retrieving historical data from JSON file: {e}')
            return None

    def build_backtest_data(self, symbol: str) -> dict:
        try:
            market_id = MarketDirectory.get_market_id(symbol)
            formatted_symbol = symbol + 'USDT'
            max_limit = 100
            rates = self.caller.get_historical_funding_rate_for_symbol(formatted_symbol, max_limit)
            for rate in rates:
                timestamp = rate['fundingTime'] // 1000
                if timestamp > MARKET_DEPLOYMENT_TIMESTAMP:
                    block_number = get_base_block_number_by_timestamp(timestamp)
                    time.sleep(0.2)
                    del rate['fundingTime']
                    rate['block_number'] = block_number
                    rate['funding_rate'] = rate['fundingRate']
                    del rate['fundingRate']
                    del rate['symbol']
                    rate['market_id'] = market_id
                else:
                    continue
            
            logger.info(f'binance rates = {rates}')
            return rates
        
        except Exception as e:
            logger.error(f'BinanceBacktester - Error while building backtesting data: {e}')
            return None


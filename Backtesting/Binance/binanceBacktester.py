import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from APICaller.Binance.binanceCaller import BinanceCaller
from Backtesting.utils.backtestingUtils import *
from Backtesting.Binance.binanceBacktesterUtils import *
from GlobalUtils.logger import logger
import math

class BinanceBacktester:
    BOUND_CONST: float = 0.68 ## 2 std. devs

    def __init__(self):
        self.caller = BinanceCaller()

    def build_statistics_dict(self, symbol: str) -> dict:
        max_limit = 1000
        rates = self.caller.get_historical_funding_rate_for_symbol(symbol, max_limit)
        past_week_average = self._get_past_week_average_rate(rates)
        past_month_average = self._get_past_month_average_rate(rates)
        past_year_average = self._get_past_year_average_rate(rates)
        average_period_out_of_bounds = self._get_average_duration_above_mean(rates=rates, mean=past_year_average)
        active_out_of_bounds_streak = self._get_current_out_of_bounds_streak(past_year_average, rates)
        open_interest_differential_usd = self._get_open_interest_usd_with_differential(symbol)
        effective_apr = calculate_effective_apr(float(rates[0]['fundingRate']))

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
            'effective_apr': effective_apr
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
            differential_usd = calculate_open_interest_differential_usd(float(open_interest_info['ratio']), float(open_interest_info['open_interest']), current_price)
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
        

x = BinanceBacktester()
y = x.build_statistics_dict(symbol='ETHUSDT')
print(y)


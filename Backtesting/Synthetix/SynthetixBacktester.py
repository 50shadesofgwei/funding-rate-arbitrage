from Backtesting.utils.backtestingUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import *
from APICaller.Synthetix.SynthetixCaller import SynthetixCaller
from GlobalUtils.globalUtils import *
from web3 import *
import math

class SynthetixBacktester:
    def __init__(self):
        self.caller = SynthetixCaller()
        self.contract = get_perps_contract()

    def build_statistics_dict(self, symbol: str) -> dict:
        rates = self.retrieve_and_process_events()
        past_week_average = self._get_past_week_average_rate(rates)
        past_month_average = self._get_past_month_average_rate(rates)
        past_year_average = self._get_past_year_average_rate(rates)
        average_period_out_of_bounds = self._get_average_duration_above_mean(rates=rates, mean=past_year_average)
        active_out_of_bounds_streak = self._get_current_out_of_bounds_streak(past_year_average, rates)
        open_interest_differential_usd = self._get_open_interest_usd_with_differential(symbol)
        effective_apr = calculate_effective_apr(float(rates[0]['funding_rate']))

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

    def _get_average_duration_above_mean(self, rates: list, mean: float):
        lower_bound = mean * (1 - BOUND_CONST)
        upper_bound = mean * (1 + BOUND_CONST)

        out_of_bounds_durations = []
        current_duration = 0
        out_of_bounds = False

        for rate in rates:
            funding_rate = float(rate['funding_rate'])
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

    def _get_current_out_of_bounds_streak(self, mean: float, data: list) -> int:
            lower_bound = mean * (1 - BOUND_CONST)
            upper_bound = mean * (1 + BOUND_CONST)

            current_streak = 0

            for rate in reversed(data):
                funding_rate = float(rate['funding_rate'])
                if funding_rate < lower_bound or funding_rate > upper_bound:
                    current_streak += 1
                else:
                    break

            return current_streak
    
    def _get_open_interest_usd_with_differential(self, symbol):
        try:
            open_interest_info = self.get_current_open_interest(symbol)
            open_interest_usd = float(open_interest_info['size'] * float(open_interest_info['price']))
            skew_usd = float(open_interest_info['skew'] * float(open_interest_info['price']))
            if open_interest_info is None or open_interest_info['price'] is None:
                raise ValueError("SynthetixBacktester - Failed to fetch open interest or current price from API.")

            data = {
                'open_interest_usd': open_interest_usd,
                'differential_usd': skew_usd,
                'ratio': open_interest_info['ratio']
            }
            return data
        except Exception as e:
            logger.info(f"SynthetixBacktester - Error calculating dollar value of open interest for {symbol}: {e}")
            return None

    def retrieve_and_process_events(self) -> list:
        """
        Retrieve events in batches and process them.
        """
        try:
            current_block = client.eth.block_number
            start_block = max(current_block - 1_000_000, 0)  
            step_size = 1_000_000 

            all_parsed_events = []

            for block in range(start_block, current_block, step_size):
                end_block = min(block + step_size, current_block)
                print(f"Fetching events from {block} to {end_block}")
                events = self.fetch_events(block, end_block)
                if events is not None:
                    parsed_events = parse_event_data(events)
                    print(f"3 - parsed events: {parsed_events}")
                    all_parsed_events.extend(parsed_events)
                else:
                    logger.error(f'events = Null for blocks {block} -> {end_block}')
            
            # Optionally save to file
            with open('parsed_events.json', 'w') as f:
                json.dump(all_parsed_events, f, indent=4)

            return all_parsed_events
        except Exception as e:
            logger.info(f"SynthetixBacktester - Error while retrieving historical events from node: {e}")
            return None

    def fetch_events(self, start_block, end_block):
        """
        Fetch events from the contract within a specified block range.
        """
        contract = get_perps_contract()
        try:
            event_filter = contract.events.MarketUpdated.create_filter(fromBlock=start_block, toBlock=end_block)
            events = event_filter.get_all_entries()
            if events is not None:
                return events
        except Exception as e:
            logger.error(f"Error fetching events from block {start_block} to {end_block}: {e}")
            return []

    def get_current_open_interest(self, symbol: str):
        response = self.caller.client.perps.get_market_summary(market_name=symbol)
        data = {
            'symbol': symbol,
            'size': response['size'],
            'max_open_interest': response['max_open_interest'],
            'skew': response['skew'],
            'price': response['index_price'],
            'ratio': self._get_long_short_ratio(response)
        }
        
        return data

    def _get_long_short_ratio(self, market_summary) -> float:
        size = float(market_summary['size'])
        skew = float(market_summary['skew'])
        half_size = size / 2
        half_size_with_skew = half_size + skew
        long_short_ratio = round(half_size_with_skew / half_size, 3)

        return long_short_ratio

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
        current_block = client.eth.block_number
        start_block = current_block - (period_days * 43200)  # 43200 blocks per day for a 2-second block time
        
        filtered_rates = [rate for rate in rates if rate['block_number'] >= start_block]
        
        if not filtered_rates:  
            return float('nan')  
        
        rate_total = sum(float(rate['funding_rate']) for rate in filtered_rates)
        num_rates = len(filtered_rates)
        
        mean_rate_for_period = rate_total / num_rates
        return mean_rate_for_period

# x = SynthetixBacktester()
# y = x.retrieve_and_process_events()
# print(y)

        

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
        try:
            rates = self.retrieve_and_process_events()
            current_vs_historical_data = self.build_current_vs_historical_rates_dict(rates)
            open_interest_differential_usd = self._get_open_interest_usd_with_differential(symbol)
            keeper_fees = self.estimate_keeper_fees()
            effective_apr = calculate_effective_apr(float(rates[-1]['funding_rate']))

            stats = {
                'symbol': symbol,
                'long_short_ratio': open_interest_differential_usd['ratio'],
                'open_interest_usd': open_interest_differential_usd['open_interest_usd'],
                'open_interest_differential_usd': open_interest_differential_usd['differential_usd'],
                'profitability_estimations': {
                    'total_estimated_profit_usd': None,
                    'total_estimated_profit_percentage': None,
                    'first_period_return_usd': None,
                    'second_period_return_usd': None,
                    'total_percentage_return': None,
                    'estimated_keeper_fees_usd': keeper_fees
                },

            }
            return stats

        except Exception as e:
            logger.error(f"SynthetixBacktester - Error building statistics dict: {e}")
            return None

    def estimate_fill_price(self, symbol: str, size: int) -> float:
        pass

    def estimate_keeper_fees(self) -> float:
        gas_price = int(self.caller.client.web3.eth.gas_price)
        eth_price = get_asset_price('ethereum')
        gwei_price = eth_price / 10**9
        print(f'gwei_price = {gwei_price}')
        estimated_keeper_fees_gwei = (gas_price * MULTICALL_GAS) / 10**9
        entry_gas = float(estimated_keeper_fees_gwei) * gwei_price
        entry_exit_gas_usd = entry_gas * 2
        print(f'SynthetixBacktester - Estimated usd keeper fee = {entry_exit_gas_usd}')

    def build_current_vs_historical_rates_dict(self, rates: list) -> dict:
        try:
            current_data = self._get_current_rate_data(rates)
            weekly_avg = self._get_past_week_average_rate(rates)
            monthly_avg = self._get_past_month_average_rate(rates)
            yearly_avg = self._get_past_year_average_rate(rates)
            historical_data = {
                'weekly_average': weekly_avg,
                'monthly_average': monthly_avg,
                'yearly_average': yearly_avg
            }

            data = {
                'current_data': current_data,
                'historical_data': historical_data
            }

            logger.info(f'DATA DICT: {data}')
            return None
        except Exception as e:
            logger.error('some error')

    def _get_current_rate_data(self, rates: list) -> float:
        try:
            most_recent = rates[-1]
            current_rate = most_recent['funding_rate']
            current_velocity = most_recent['funding_velocity']
            current_skew = float(most_recent['skew'])

            data = {
                'current_rate': current_rate,
                'current_velocity': current_velocity,
                'current_skew': current_skew
            }
            return data
        except Exception as e:
            logger.error(f"SynthetixBacktester - Error retrieving latest rate data from rates list: {e}")
            return None

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
                logger.info(f"SynthetixBacktester - Fetching events from {block} to {end_block}")
                events = self.fetch_events(block, end_block)
                if events is not None:
                    parsed_events = parse_event_data(events)
                    all_parsed_events.extend(parsed_events)
                else:
                    logger.error(f'SynthetixBacktester - events = Null for blocks {block} -> {end_block}')

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
        average_rate = self._calculate_average_funding_rate(period_days=7, rates=rates)
        return average_rate

    def _get_past_month_average_rate(self, rates: list) -> float:
        average_rate = self._calculate_average_funding_rate(period_days=30, rates=rates)
        return average_rate

    def _get_past_year_average_rate(self, rates: list) -> float:
        average_rate = self._calculate_average_funding_rate(period_days=math.floor(1000/3), rates=rates)
        return average_rate

    def _calculate_average_funding_rate(symbol: str, period_days: int, rates: list, blocks_per_sample=100) -> float:
        market_id = MarketDirectory.get_market_id(symbol)

        current_block = client.eth.block_number
        start_block = current_block - (period_days * 43200)  # 43200 blocks per day

        filtered_rates = sorted(
            (rate for rate in rates if rate['block_number'] >= start_block and rate['market_id'] == market_id),
            key=lambda x: x['block_number']
        )

        if not filtered_rates:
            return float('nan')

        sampled_rates = []
        
        for i in range(len(filtered_rates) - 1):
            start_rate_info = filtered_rates[i]
            end_rate_info = filtered_rates[i + 1]
            start_rate = float(start_rate_info['funding_rate'])
            end_rate = float(end_rate_info['funding_rate'])
            start_rate_block = start_rate_info['block_number']
            end_rate_block = end_rate_info['block_number']

            gradient = (end_rate - start_rate) / (end_rate_block - start_rate_block)

            for block in range(start_rate_block, end_rate_block, blocks_per_sample):
                interpolated_rate = start_rate + gradient * (block - start_rate_block)
                sampled_rates.append(interpolated_rate)

        sampled_rates.append(float(filtered_rates[-1]['funding_rate']))
        
        average_rate = sum(sampled_rates) / len(sampled_rates)

        return average_rate

x = SynthetixBacktester()
y = x.build_statistics_dict('ethereum')

            

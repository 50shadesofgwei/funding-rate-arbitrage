from Backtesting.utils.backtestingUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import *
from APICaller.Synthetix.SynthetixCaller import SynthetixCaller
from GlobalUtils.globalUtils import *
from GlobalUtils.marketDirectory import MarketDirectory
from APICaller.master.MasterUtils import TARGET_TOKENS
from web3 import *
import math

class SynthetixBacktester:
    def __init__(self):
        self.caller = SynthetixCaller()
        self.contract = get_perps_contract()

    def build_statistics_dict(self, symbol: str) -> dict:
        try:
            rates = self.retrieve_and_process_events(symbol)
            processed_rates = preprocess_rates(rates)
            current_vs_historical_data = self.build_current_vs_historical_rates_dict(rates=processed_rates)
            open_interest_differential_usd = self._get_open_interest_usd_with_differential(symbol)
            keeper_fees = self.estimate_keeper_fees()

            stats = {
                'symbol': symbol,
                'long_short_ratio': open_interest_differential_usd['ratio'],
                'open_interest_usd': open_interest_differential_usd['open_interest_usd'],
                'open_interest_differential_usd': open_interest_differential_usd['differential_usd'],
                'rate_data': current_vs_historical_data,
                'profitability_estimations': {
                    'total_estimated_profit_usd': None,
                    'total_estimated_profit_percentage': None,
                    'first_period_return_usd': None,
                    'second_period_return_usd': None,
                    'total_percentage_return': None,
                    'estimated_keeper_fees_usd': keeper_fees
                },

            }
            logger.info(f'statistics dictionary built as shown: {stats}')
            return stats

        except Exception as e:
            logger.error(f"SynthetixBacktester - Error building statistics dict: {e}")
            return None

    def estimate_keeper_fees(self) -> float:
        gas_price = int(self.caller.client.web3.eth.gas_price)
        eth_price = get_price_from_pyth(self.caller.client, 'ETH')
        gwei_price = eth_price / 10**9
        estimated_keeper_fees_gwei = (gas_price * MULTICALL_GAS) / 10**9
        entry_gas = float(estimated_keeper_fees_gwei) * gwei_price
        entry_exit_gas_usd = entry_gas * 2

        return entry_exit_gas_usd

    def build_current_vs_historical_rates_dict(self, rates: list) -> dict:
        try:
            current_data = self._get_current_rate_data(rates)
            weekly_avg = self._get_past_week_average_rate(rates)
            monthly_avg = self._get_past_month_average_rate(rates)
            yearly_avg = self._get_past_year_average_rate(rates)
            average_out_of_bounds_duration = self._get_average_duration_above_mean(rates, monthly_avg)
            current_streak = self._get_current_out_of_bounds_streak(monthly_avg, rates)
            historical_data = {
                'weekly_average': weekly_avg,
                'monthly_average': monthly_avg,
                'yearly_average': yearly_avg,
                'average_consecutive_blocks_out_of_bounds': average_out_of_bounds_duration,
                'current_out_of_bounds_streak': current_streak
            }

            data = {
                'current_data': current_data,
                'historical_data': historical_data
            }

            return data
        except Exception as e:
            logger.error(f'SynthetixBacktester - Error while building current vs historical rate dictionary: {e}')

    def _get_current_rate_data(self, rates: list) -> dict:
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
            logger.info(f'current rate data: {data}')
            return data
        except Exception as e:
            logger.error(f"SynthetixBacktester - Error retrieving latest rate data from rates list: {e}")
            return None

    def _get_average_duration_above_mean(self, rates: list, mean: float):
        lower_bound = mean * (1 - BOUND_CONST)
        upper_bound = mean * (1 + BOUND_CONST)

        out_of_bounds_durations = []
        start_block_number = None
        out_of_bounds = False

        for rate in rates:
            funding_rate = float(rate['funding_rate'])
            block_number = rate['block_number']
            if funding_rate < lower_bound or funding_rate > upper_bound:
                if not out_of_bounds:
                    out_of_bounds = True
                    start_block_number = block_number
            else:
                if out_of_bounds:
                    duration = block_number - start_block_number
                    out_of_bounds_durations.append(duration)
                    out_of_bounds = False
                    start_block_number = None

        if out_of_bounds:
            last_block_number = rates[-1]['block_number']
            duration = last_block_number - start_block_number
            out_of_bounds_durations.append(duration)

        if out_of_bounds_durations:
            average_duration = sum(out_of_bounds_durations) / len(out_of_bounds_durations)
        else:
            average_duration = 0

        return average_duration

    def _get_current_out_of_bounds_streak(self, mean: float, rates: list) -> int:
        lower_bound = mean * (1 - BOUND_CONST)
        upper_bound = mean * (1 + BOUND_CONST)
        out_of_bounds = False
        start_block_number = None
        total_duration = 0

        for rate in rates:
            funding_rate = float(rate['funding_rate'])
            block_number = rate['block_number']

            if funding_rate < lower_bound or funding_rate > upper_bound:
                if not out_of_bounds:
                    out_of_bounds = True
                    start_block_number = block_number
            else:
                if out_of_bounds:
                    if start_block_number is not None:
                        duration = block_number - start_block_number
                        total_duration += duration
                        out_of_bounds = False

        if out_of_bounds and start_block_number is not None:
            last_block_number = rates[-1]['block_number']
            total_duration += last_block_number - start_block_number

        return total_duration

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

    def fetch_and_process_events_for_all_tokens(self):
        try:
            events = self.fetch_all_events()
            self.process_events_for_all_symbols(events)

        except Exception as e:
            logger.error(f"SynthetixBacktester - Error fetching or processing events for all symbols: {e}")
            return

    def process_events_for_all_symbols(self, parsed_events: list):
        try:
            for token_info in TARGET_TOKENS:
                symbol = token_info["token"]
                if token_info["is_target"]:
                    market_id = MarketDirectory.get_market_id(symbol)
                    market_events = [event for event in parsed_events if event.get('market_id') == market_id]
                    save_data_to_json(market_events, symbol)
                    logger.info(f"SynthetixBacktester - Processed {len(market_events)} events for symbol {symbol}")

            return
        except Exception as e:
            logger.error(f"SynthetixBacktester - Error processing events for all symbols: {e}")
            return 

    def fetch_all_events(self) -> list:
        try:
            current_block = client.eth.block_number
            start_block = max(current_block - 1000000, 0)
            step_size = 10000
            all_events = []
            
            for block in range(start_block, current_block, step_size):
                current_end_block = min(block + step_size - 1, current_block)
                logger.info(f"Fetching events from block {block} to {current_end_block}")
                events = self.fetch_events_for_block_range(block, current_end_block)
                if events:
                    parsed_events = parse_event_data(events)
                    all_events.extend(parsed_events)
                else:
                    logger.error(f"SynthetixBacktester - No events found from blocks {block} to {current_end_block}")
                    
            return all_events
        except Exception as e:
            logger.error(f"SynthetixBacktester - Error while retrieving historical events from node: {e}")
            return []

    def fetch_events_for_block_range(self, start_block, end_block):
        contract = get_perps_contract()
        try:
            event_filter = contract.events.MarketUpdated.create_filter(fromBlock=start_block, toBlock=end_block)
            events = event_filter.get_all_entries()
            if events is not None:
                return events
        except Exception as e:
            logger.error(f"SynthetixBacktester - Error fetching events from block {start_block} to {end_block}: {e}")
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
        year = int(math.floor(1000/3))
        average_rate = self._calculate_average_funding_rate(period_days=year, rates=rates)
        return average_rate

    def _calculate_average_funding_rate(self, period_days: int, rates: list, blocks_per_sample=1) -> float:
        try:
            current_block = client.eth.block_number
            start_block = current_block - (period_days * BLOCKS_PER_DAY_BASE)

            filtered_rates = sorted(
            (rate for rate in rates if rate['block_number'] >= start_block),
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

                if end_rate_block == start_rate_block:
                    logger.info(f'SynthetixBacktester - Identical block numbers encountered: {start_rate_block}')
                    continue

                gradient = (end_rate - start_rate) / (end_rate_block - start_rate_block)

                for block in range(start_rate_block, end_rate_block, blocks_per_sample):
                    interpolated_rate = start_rate + gradient * (block - start_rate_block)
                    sampled_rates.append(interpolated_rate)

            sampled_rates.append(float(filtered_rates[-1]['funding_rate']))
            average_rate = sum(sampled_rates) / len(sampled_rates)

            return average_rate
        
        except Exception as e:
            logger.error(f'SynthetixBacktester - Error while calculating average funding rate: {e}')
            return 0.0

    def load_data_from_json(self, symbol: str):
        try:
            filename = f'Backtesting/MasterBacktester/historicalDataJSON/Synthetix/{symbol}Historical.json'
            with open(filename, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f'SynthetixBacktester - Error while retriving historical data from JSON file: {e}')
            return
            

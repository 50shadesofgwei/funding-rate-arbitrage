from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from APICaller.GMX.GMXCallerUtils import *
set_paths()

class GMXCaller:
    def __init__(self):
        self.stats_caller = build_stats_class()
        self.config = ARBITRUM_CONFIG_OBJECT

    def get_funding_rates(self, symbols: list) -> list:
        try:
            raw_opportunities = self.get_opportunities_raw()
            parsed_opportunities = parse_opportunity_objects_from_response(raw_opportunities)
            filtered_opportunities = filter_market_data(parsed_opportunities, symbols)

            return filtered_opportunities
        
        except Exception as e:
            logger.error(f'GMXCaller - Failed to get funding rates. Error: {e}')
            return None


    def get_opportunities_raw(self):
        try:
            data_raw = self._collect_data_raw()
            net_rates = self._calculate_net_rates(data_raw['borrow_apr'], data_raw['funding_apr'])
            liquidity = data_raw['liquidity']
            nested = self._create_nested_dict(liquidity, net_rates)
            sorted = self.get_sorted_keys(nested)
            open_interest = data_raw['open_interest']
            dict_of_opportunities = self._analyze_opportunities(
                    sorted, nested, open_interest)

            return dict_of_opportunities

        except Exception as e:
            logger.error(f'GMXCaller - Failed to get raw opportunities object. Error: {e}')
            return None

    def _analyze_opportunities(self, sorted_keys: list, nested_dict: dict, open_interest_data: dict):
        try:
            dict_of_opportunities = {"long": {}, "short": {}}

            for i, key in enumerate(sorted_keys, 1):
                net_rate_per_hour = nested_dict[key]['net_rate']
                if net_rate_per_hour < 0:
                    continue
                liquidity = nested_dict[key]['liquidity']

                position_type, asset = key.split('_')
                focus_direction = "long" if position_type == "long" else "short"
                opposite_side = "short" if position_type == "long" else "long"

                oi_imbalance = open_interest_data[opposite_side][asset] - \
                    open_interest_data[focus_direction][asset]


                dict_of_opportunities[position_type][asset] = {
                    "net_rate_per_hour": net_rate_per_hour,
                    "available_liquidity": liquidity,
                    "open_interest_imbalance": oi_imbalance
                }


            return dict_of_opportunities

        except KeyError as ke:
            logger.error(f'GMXCaller - KeyError encountered while analyzing opportunities. Error: {ke}')
            return None
        except Exception as e:
            logger.error(f'GMXCaller - Failed to analyze opportunities. Error: {e}')
            return None


    def get_sorted_keys(self, nested_dict: dict) -> list:
        try:
            sorted_keys = sort_nested_dict(nested_dict)
            return sorted_keys
        
        except Exception as e:
            logger.error(f'GMXCaller - Failed to sort nested dictionary. Error: {e}')
            return None

    def _create_nested_dict(self, available_liquidity: dict, net_rate_dict: dict) -> dict:
        try:
            liquidity_dict = {'long_{}'.format(key): value for key,
                            value in available_liquidity['long'].items()}
            liquidity_dict.update({'short_{}'.format(key): value for key,
                                value in available_liquidity['short'].items()})
            nested_dict = {}

            for key in liquidity_dict:
                position_type, asset = key.split('_')
                new_key = "{}_{}".format(position_type, asset)
                nested_dict[new_key] = {'liquidity': liquidity_dict[key], 'net_rate': net_rate_dict[key]}

            return nested_dict

        except KeyError as ke:
            logger.error(f'GMXCaller - KeyError encountered while creating nested dictionary from available_liquidity and net_rate_dict objects. Error: {ke}')
            return None
        except Exception as e:
            logger.error(f'GMXCaller - Failed to create nested dictionary from available_liquidity and net_rate_dict objects. Error: {e}')
            return None

    def _calculate_net_rates(self, borrow_data: dict, funding_data: dict) -> dict:
        try:
            long_net_rates = {key: borrow_data['long'][key] * -1 +
                        funding_data['long'][key] for key in borrow_data['long']}
            short_net_rates = {key: borrow_data['short'][key] * -1 +
                            funding_data['short'][key] for key in borrow_data['short']}

            net_rate_dict = {'long_{}'.format(key): value for key, value in long_net_rates.items()}
            net_rate_dict.update({'short_{}'.format(key): value for key, value in short_net_rates.items()})

            return net_rate_dict

        except Exception as e:
            logger.error(f'GMXCaller - Failed to calculate net rates from raw data from GMX. Error: {e}')
            return None
    
    def _collect_data_raw(self) -> dict:
        try:
            liquidity = self.stats_caller.get_available_liquidity()
            time.sleep(0.5)
            borrow_apr = self.stats_caller.get_borrow_apr()
            time.sleep(0.5)
            funding_apr = self.stats_caller.get_funding_apr()
            time.sleep(0.5)
            open_interest = self.stats_caller.get_open_interest()

            data_raw = {
                'liquidity': liquidity,
                'borrow_apr': borrow_apr,
                'funding_apr': funding_apr,
                'open_interest': open_interest
            }

            return data_raw

        except Exception as e:
            logger.error(f'GMXCaller - Failed to collect raw data from GMX. Error: {e}')
            return None
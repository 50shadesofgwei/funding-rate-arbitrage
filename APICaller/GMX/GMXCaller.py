from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from APICaller.GMX.GMXCallerUtils import *
import pandas as pd
set_paths()

from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager

class GMXCaller:
    def __init__(self):
        self.stats_caller = build_stats_class(chain='arbitrum')
        self.config = ConfigManager(chain='arbitrum')
        self.config.set_config(filepath='/Users/jfeasby/SynthetixFundingRateArbitrage/config.yaml')

    def get_funding_rates(self, symbols: list) -> dict:
        if not symbols:
            logger.error("GMXCaller - No symbols provided to fetch funding rates.")
            return None

    def check_if_viable_farming_strategy(self, parameters: dict, ignore_oi_imbalance=False):
        asset = parameters['index_token_symbol']
        collateral = parameters['collateral_token_symbol']
        is_long = parameters['is_long']
        is_delta_neutral = parameters['is_delta_neutral']
        position_size_usd = parameters['size_delta'] / 10**30
        direction = 'Short'
        if is_long:
            direction = 'Long'

        dn_insert = "." if not is_delta_neutral else ", while remaining delta neutral!"

        print("Requesting to open ${} {} on {}{}\n\n".format(
            numerize.numerize(position_size_usd),
            direction,
            asset,
            dn_insert
        ))
        print("---------------------------")
        if asset not in collateral or direction != "Short":
            if is_delta_neutral:
                raise Exception("Asset must = collateral AND direction = short to be Delta Neutral..")

        dict_of_opportunities = self.get_opportunities_raw()

        print("---------------------------")

        try:
            stats = dict_of_opportunities[direction.lower()][asset]
        except KeyError:
            raise Exception('No opportunity for farming "{} {}"!'.format(asset, direction))

        if position_size_usd > stats['open_interest_imbalance'] and not ignore_oi_imbalance:
            raise Exception("Opening a position size of ${} will tip open interest balance in opposite direction!".format(
                numerize.numerize(position_size_usd)
            ))

        if stats["net_rate_per_hour"] < parameters["net_rate_threshold"]:
            raise Exception("Net Rate of {:.3f} does not meet requirement of {}".format(
                stats["net_rate_per_hour"], parameters["net_rate_threshold"]
            ))
        usd_earning_per_hour = numerize.numerize(stats["net_rate_per_hour"] / 100 * position_size_usd)
        print("\n\nPosition viable, and will net ${} per hour.".format(usd_earning_per_hour))
        return stats

    def get_opportunities_raw(self):
        try:
            data_raw = self._collect_data_raw()
            net_rates = self._calculate_net_rates(data_raw['borrow_apr'], data_raw['funding_apr'])
            liquidity = data_raw['liquidity']
            nested = self._create_nested_dict(liquidity, net_rates)
            sorted = self.get_sorted_keys(nested)
            logger.info(f'sorted keys = {sorted}')
            dict_of_opportunities = self._analyze_opportunities(
                    sorted, nested, data_raw['open_interest'])

            for name, value in [data_raw, net_rates, nested, sorted]:
                if value is None:
                    logger.error(f'GMXCaller - None value returned during data collection in get_opportunities_raw: {name} object = None')


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
            markets = self.stats_caller.get_available_markets()
            liquidity = self.stats_caller.get_available_liquidity()
            liquidity = pd.DataFrame.to_dict(liquidity)
            borrow_apr = self.stats_caller.get_borrow_apr()
            borrow_apr = pd.DataFrame.to_dict(borrow_apr)
            claimable_fees = self.stats_caller.get_claimable_fees()
            claimable_fees = pd.DataFrame.to_dict(claimable_fees)
            funding_apr = self.stats_caller.get_funding_apr()
            funding_apr = pd.DataFrame.to_dict(funding_apr)
            gm_prices = self.stats_caller.get_gm_price()
            open_interest = self.stats_caller.get_open_interest()
            open_interest = pd.DataFrame.to_dict(open_interest)

            data_raw = {
                'markets': markets,
                'liquidity': liquidity,
                'borrow_apr': borrow_apr,
                'claimable_fees': claimable_fees,
                'funding_apr': funding_apr,
                'gm_prices': gm_prices,
                'open_interest': open_interest
            }

            for name, value in data_raw.items():
                if value is None:
                    logger.error(f'GMXCaller - None value returned during data collection: {name} object = None')

            return data_raw

        except Exception as e:
            logger.error(f'GMXCaller - Failed to collect raw data from GMX. Error: {e}')
            return None

x = GMXCaller()
y = x.get_opportunities_raw()
for op in y.items():
    z = x.check_if_viable_farming_strategy(op)
    print(z)
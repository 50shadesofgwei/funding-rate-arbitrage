from gmx_python_sdk.scripts.v2.gmx_utils import ConfigManager
import time
import sys
import os
from numerize import numerize
from gmx_python_sdk.scripts.v2.get.get_available_liquidity import (
    GetAvailableLiquidity
)
from gmx_python_sdk.scripts.v2.get.get_borrow_apr import GetBorrowAPR
from gmx_python_sdk.scripts.v2.get.get_funding_apr import GetFundingFee
from gmx_python_sdk.scripts.v2.get.get_open_interest import OpenInterest
from GlobalUtils.logger import logger

def set_paths():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(current_dir, '../')
    sys.path.append(target_dir)

set_paths()


arbitrum_config_object = ConfigManager(chain='arbitrum')
arbitrum_config_object.set_config('/Users/jfeasby/SynthetixFundingRateArbitrage/config.yaml')

def get_data(chain: str = 'arbitrum'):
    """
    Retrieve relevant data for farming analysis.

    Parameters:
    chain (str) The blockchain chain (default: 'arbitrum').
    Returns:
        Tuple:
        Tuple containing funding data, borrow data, available liquidity, and open interest data.
    """
    funding_data = GetFundingFee(arbitrum_config_object).get_data()
    time.sleep(0.5)
    borrow_data = GetBorrowAPR(chain=chain).get_data()
    time.sleep(0.5)
    available_liquidity = GetAvailableLiquidity(chain=chain).get_data()
    time.sleep(0.5)
    open_interest_data = OpenInterest(chain=chain).get_data()

    return funding_data, borrow_data, available_liquidity, open_interest_data


def calculate_net_rates(borrow_data: dict, funding_data: dict):
    """
    Calculate net rates for long and short positions.

    Parameters:
    - borrow_data (dict): Borrow APR data.
    - funding_data (dict): Funding APR data.

    Returns:
    dict: Dictionary containing net rates for both long and short positions.
    """
    long_net_rates = {key: borrow_data['long'][key] * -1 +
                      funding_data['long'][key] for key in borrow_data['long']}
    short_net_rates = {key: borrow_data['short'][key] * -1 +
                       funding_data['short'][key] for key in borrow_data['short']}

    net_rate_dict = {'long_{}'.format(key): value for key, value in long_net_rates.items()}
    net_rate_dict.update({'short_{}'.format(key): value for key, value in short_net_rates.items()})

    return net_rate_dict


def create_nested_dict(available_liquidity: dict, net_rate_dict: dict):
    """
    Create a nested dictionary containing liquidity and net rates.

    Parameters:
    - available_liquidity (dict): Available liquidity data.
    - net_rate_dict (dict): Net rate data.

    Returns:
    dict: Nested dictionary with liquidity and net rates.
    """
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


def sort_nested_dict(nested_dict: dict):
    """
    Sort the nested dictionary keys by the highest net rate.

    Parameters:
    - nested_dict (dict): Nested dictionary with liquidity and net rates.

    Returns:
    list: List of sorted keys.
    """
    # Sort keys by the highest net rate
    sorted_keys = sorted(nested_dict.keys(), key=lambda k: nested_dict[k]['net_rate'], reverse=True)
    return sorted_keys


def analyze_opportunities(sorted_keys: list, nested_dict: dict, open_interest_data: dict):
    """
    Analyze farming opportunities based on sorted keys.

    Parameters:
    - sorted_keys (list): List of sorted keys.
    - nested_dict (dict): Nested dictionary with liquidity and net rates.
    - open_interest_data (dict): Open interest data.

    Returns:
    Tuple:
        Tuple containing a string of ranked opportunities and a dictionary of opportunities.
    """
    list_of_opportunities_str = "Ranked Farming Opportunities (By net rate/hour)"
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

        opportunity = "\n\n{}) {} {}\n\nRate/hour: {:.4f}%\nAvailable Liquidity: ${}\nOpen Interest Imbalance toward {}: ${}\n\n---------------".format(
            i,
            asset,
            position_type,
            net_rate_per_hour,
            numerize.numerize(liquidity),
            opposite_side.title(),
            numerize.numerize(oi_imbalance)
        )

        dict_of_opportunities[position_type][asset] = {
            "net_rate_per_hour": net_rate_per_hour,
            "available_liquidity": liquidity,
            "open_interest_imbalance": oi_imbalance
        }

        list_of_opportunities_str += opportunity

    return list_of_opportunities_str, dict_of_opportunities


def get_opportunities():
    """
    Get farming opportunities.

    Returns:
    dict: Dictionary containing farming opportunities.
    """
    funding_data, borrow_data, available_liquidity, open_interest_data = get_data()
    net_rate_dict = calculate_net_rates(borrow_data, funding_data)
    nested_dict = create_nested_dict(available_liquidity, net_rate_dict)
    sorted_keys = sort_nested_dict(nested_dict)
    list_of_opportunities, dict_of_opportunities = analyze_opportunities(
        sorted_keys, nested_dict, open_interest_data)

    return dict_of_opportunities


def check_if_viable_farming_strategy(parameters: dict, ignore_oi_imbalance=False):
    """
    A dictionary of parameters containing information on the asset, collateral, direction,
    request to be delta neutral, and position size.

    Optional flags to ignore warnings.

    Parameters
    ----------
    parameters : dict
        DESCRIPTION.


    """

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

    dict_of_opportunities = get_opportunities()

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

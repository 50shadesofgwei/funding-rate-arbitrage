from APICaller.GMX.GMXContractUtils import DATASTORE_CONTRACT_OBJECT
from APICaller.GMX.GMXCallerUtils import ARBITRUM_CONFIG_OBJECT
from gmx_python_sdk.scripts.v2.get.get_funding_apr import *

def get_variables_for_funding_rate_calculations(symbol: str):

    data = DATASTORE_CONTRACT_OBJECT.functions.getUint


def determine_new_funding_rate(
        funding_factor_per_second: float,
        skew_usd: float,
        funding_exponent_factor: float,
        total_open_interest_usd: float
    ) -> float:

    pass


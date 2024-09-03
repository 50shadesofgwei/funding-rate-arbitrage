from APICaller.Synthetix.SynthetixUtils import get_synthetix_client
from APICaller.Binance.binanceUtils import get_binance_client
from APICaller.HMX.HMXCallerUtils import get_HMX_client
from APICaller.ByBit.ByBitUtils import get_ByBit_client

GLOBAL_SYNTHETIX_CLIENT = get_synthetix_client()
GLOBAL_BYBIT_CLIENT = get_ByBit_client()
GLOBAL_HMX_CLIENT = get_HMX_client()
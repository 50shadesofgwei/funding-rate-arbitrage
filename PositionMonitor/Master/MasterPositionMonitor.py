import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from PositionMonitor.Synthetix.SynthetixPositionMonitor import SynthetixPositionMonitor
from PositionMonitor.Binance.BinancePositionMonitor import BinancePositionMonitor
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from pubsub import pub
import threading
import time


class MasterPositionMonitor():
    def __init__(self):
        self.synthetix = SynthetixPositionMonitor()
        self.binance = BinancePositionMonitor()
        self.health_check_thread = None
        self.stop_health_check = threading.Event()
        
        pub.subscribe(self.on_position_opened, eventsDirectory.POSITION_OPENED.value)
        pub.subscribe(self.on_position_closed, eventsDirectory.POSITION_CLOSED.value)

    @log_function_call
    def on_position_opened(self, position_data):
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            time.sleep(10)
            self.stop_health_check.clear()  
            self.health_check_thread = threading.Thread(target=self.start_health_check, daemon=True)
            self.health_check_thread.start()
        else:
            logger.info('MasterPositionMonitor - Health check already running.')

    @log_function_call
    def on_position_closed(self, position_report):
        self.stop_health_check.set()

    @log_function_call
    def start_health_check(self):
        while not self.stop_health_check.is_set():
            self.position_health_check()
            time.sleep(30)

    @log_function_call
    def position_health_check(self):
        is_liquidation_risk = self.check_liquidation_risk()
        is_profitable = self.check_profitability_for_open_position()
        is_delta_within_bounds = self.is_position_delta_within_bounds()

        if is_liquidation_risk:
            reason = PositionCloseReason.LIQUIDATION_RISK.value
            pub.sendMessage(eventsDirectory.CLOSE_ALL_POSITIONS.value, reason=reason)
        elif not is_profitable:
            reason = PositionCloseReason.NO_LONGER_PROFITABLE.value
            pub.sendMessage(eventsDirectory.CLOSE_ALL_POSITIONS.value, reason=reason)
        elif not is_delta_within_bounds:
            reason = PositionCloseReason.DELTA_ABOVE_BOUND.value
            pub.sendMessage(eventsDirectory.CLOSE_ALL_POSITIONS.value, reason=reason)
        else:
            logger.info('MasterPositionMonitor - no threat detected for open position')

    @log_function_call
    def check_liquidation_risk(self) -> bool:
        try:
            synthetix_position = self.synthetix.get_open_position()
            binance_position = self.binance.get_open_position()

            is_synthetix_risk = self.synthetix.is_near_liquidation_price(synthetix_position)
            is_binance_risk = self.binance.is_near_liquidation_price(binance_position)

            if is_binance_risk or is_synthetix_risk:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error while checking liquidation risk for positions: {e}")
            return False

    @log_function_call
    def check_profitability_for_open_position(self):
        try:
            synthetix_position = self.synthetix.get_open_position()
            binance_position = self.binance.get_open_position()

            synthetix_funding_rate = self.synthetix.get_funding_rate(synthetix_position)
            binance_funding_rate = self.binance.get_funding_rate(binance_position)

            synthetix_funding_impact = calculate_funding_impact(synthetix_position, synthetix_funding_rate) if synthetix_position else 0
            binance_funding_impact = calculate_funding_impact(binance_position, binance_funding_rate) if binance_position else 0

            net_funding_impact = synthetix_funding_impact + binance_funding_impact

            is_profitable = net_funding_impact > 0
            return is_profitable
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error checking overall profitability for open positions: {e}")
            return False

    @log_function_call
    def is_position_delta_within_bounds(self):
        try:
            delta_bound = float(os.getenv('DELTA_BOUND'))
            synthetix_position = self.synthetix.get_open_position()
            binance_position = self.binance.get_open_position()

            if not synthetix_position:
                logger.error("MasterPositionMonitor - Synthetix position is missing when trying to calculate delta.")
                return False
            elif not binance_position:
                logger.error("MasterPositionMonitor - Binance position is missing when trying to calculate delta.")
                return False

            try:
                symbol = normalize_symbol(synthetix_position['symbol'])
            except KeyError as e:
                logger.error(f"MasterPositionMonitor - Missing 'symbol' key in Synthetix position details: {e}")
                return False

            try:
                full_symbol = get_full_asset_name(symbol)
            except Exception as e:
                logger.error(f"MasterPositionMonitor - Error retrieving full symbol name for {symbol}: {e}")
                return False

            try:
                asset_price = get_asset_price(asset=full_symbol)
            except Exception as e:
                logger.error(f"MasterPositionMonitor - Error retrieving asset price for {full_symbol}: {e}")
                return False

            synthetix_notional_value = float(synthetix_position['size']) * asset_price
            binance_notional_value = float(binance_position['size']) * asset_price

            synthetix_notional_value = synthetix_notional_value if synthetix_position['side'].upper() == 'LONG' else -synthetix_notional_value
            binance_notional_value = binance_notional_value if binance_position['side'].upper() == 'LONG' else -binance_notional_value

            total_notional_value = abs(synthetix_notional_value) + abs(binance_notional_value)
            delta_in_usd = abs(synthetix_notional_value - binance_notional_value)
            delta = (delta_in_usd / total_notional_value) if total_notional_value else 0

            logger.info(f'MasterPositionMonitor - Position delta calculated at {delta}')

            return delta > delta_bound
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Unexpected error in checking position delta: {e}")
            return False
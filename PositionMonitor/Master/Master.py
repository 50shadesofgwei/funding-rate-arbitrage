import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from PositionMonitor.Synthetix.SynthetixPositionMonitor import SynthetixPositionMonitor
from PositionMonitor.Binance.BinancePositionMonitor import BinancePositionMonitor
from PositionMonitor.Master.utils import *
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import *
from pubsub import pub
from threading import Thread, Event
import time


class MasterPositionMonitor():
    def __init__(self):
        self.synthetix = SynthetixPositionMonitor()
        self.binance = BinancePositionMonitor()
        self.health_check_thread = None
        self.stop_health_check = Event()
        
        pub.subscribe(self.on_position_opened, eventsDirectory.POSITION_OPENED.value)
        pub.subscribe(self.on_position_closed, eventsDirectory.POSITION_CLOSED.value)

    def on_position_opened(self, position_data):
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            self.stop_health_check.clear()
            self.health_check_thread = Thread(target=self.start_health_check)
            self.health_check_thread.start()
        else:
            logger.info('MasterPositionMonitor - Health check already running.')

    def on_position_closed(self, position_report):
        self.stop_health_check.set()
        if self.health_check_thread is not None:
            self.health_check_thread.join()

    def start_health_check(self):
        while not self.stop_health_check.is_set():
            self.position_health_check()
            time.sleep(10)

    def position_health_check(self):
        is_liquidation_risk = self.check_liquidation_risk()
        is_profitable = self.check_profitability_for_open_position()
        is_delta_within_bounds = self.is_position_delta_within_bounds()

        if is_liquidation_risk:
            reason = PositionCloseReason.LIQUIDATION_RISK.value
            pub.sendMessage(eventsDirectory.CLOSE_ALL_POSITIONS.value, reason)
        elif not is_profitable:
            reason = PositionCloseReason.NO_LONGER_PROFITABLE.value
            pub.sendMessage(eventsDirectory.CLOSE_ALL_POSITIONS.value, reason)
        elif not is_delta_within_bounds:
            reason = PositionCloseReason.DELTA_ABOVE_BOUND.value
            pub.sendMessage(eventsDirectory.CLOSE_ALL_POSITIONS.value, reason)
        else:
            logger.info('MasterPositionMonitor - no threat detected for open position')

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

    def is_position_delta_within_bounds(self):
        try:
            delta_bound = float(os.getenv('DELTA_BOUND'))
            synthetix_position = self.synthetix.get_open_position()
            binance_position = self.binance.get_open_position()

            symbol = normalize_symbol(synthetix_position['symbol'])
            full_symbol = get_full_asset_name(symbol)
            asset_price = get_asset_price(full_symbol)

            synthetix_notional_value = float(synthetix_position['size'] * asset_price)
            binance_notional_value = float(binance_position['size'] * asset_price)

            synthetix_notional_value = synthetix_notional_value if synthetix_position['side'].upper() == 'LONG' else -synthetix_notional_value
            binance_notional_value = binance_notional_value if binance_position['side'].upper() == 'LONG' else -binance_notional_value

            # Calculate delta as the difference in notional values
            total_notional_value = float(abs(synthetix_notional_value) + abs(binance_notional_value))
            delta_in_usd = abs(synthetix_notional_value - binance_notional_value)
            delta = (delta_in_usd / total_notional_value) if total_notional_value != 0 else 0

            # Check if delta is above the specified bound
            return delta < delta_bound
        except KeyError as e:
            logger.error(f"MasterPositionMonitor - Missing key in position details: {e}")
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error calculating position pair delta: {e}")

        return False

    



        


            


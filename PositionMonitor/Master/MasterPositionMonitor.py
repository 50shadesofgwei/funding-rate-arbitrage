from PositionMonitor.Synthetix.SynthetixPositionMonitor import SynthetixPositionMonitor
from PositionMonitor.Binance.BinancePositionMonitor import BinancePositionMonitor
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from GlobalUtils.marketDirectory import MarketDirectory
from pubsub import pub
import threading
import time

class MasterPositionMonitor():
    def __init__(self):
        self.synthetix = SynthetixPositionMonitor()
        self.binance = BinancePositionMonitor()
        self.health_check_thread = None
        self.stop_health_check = threading.Event()
        
        pub.subscribe(self.on_position_opened, EventsDirectory.TRADE_LOGGED.value)
        pub.subscribe(self.on_position_closed, EventsDirectory.POSITION_CLOSED.value)

    def on_position_opened(self, position_data):
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            time.sleep(10)
            self.stop_health_check.clear()  
            self.health_check_thread = threading.Thread(target=self.start_health_check, daemon=True)
            self.health_check_thread.start()
        else:
            logger.info('MasterPositionMonitor - Health check already running.')

    def on_position_closed(self, position_report):
        self.stop_health_check.set()

    def start_health_check(self):
        while not self.stop_health_check.is_set():
            self.position_health_check()
            time.sleep(30)

    def position_health_check(self):
        is_liquidation_risk = self.check_liquidation_risk()
        is_profitable = self.check_profitability_for_open_position()
        is_delta_within_bounds = self.is_position_delta_within_bounds()
        is_funding_velocity_turning = self.is_funding_turning_against_trade_in_given_time(30)

        exchanges = ['Synthetix', 'Binance']
        if is_liquidation_risk:
            reason = PositionCloseReason.LIQUIDATION_RISK.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol='ETH', reason=reason, exchanges=exchanges)
        elif not is_profitable:
            reason = PositionCloseReason.NO_LONGER_PROFITABLE.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol='ETH', reason=reason, exchanges=exchanges)
        elif not is_delta_within_bounds:
            reason = PositionCloseReason.DELTA_ABOVE_BOUND.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol='ETH', reason=reason, exchanges=exchanges)
        elif is_funding_velocity_turning:
            reason = PositionCloseReason.FUNDING_TURNING_AGAINST_TRADE.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol='ETH', reason=reason, exchanges=exchanges)
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

    def check_profitability_for_open_position(self) -> bool:
        try:
            synthetix_position = self.synthetix.get_open_position()

            if not synthetix_position:
                logger.info("MasterPositionMonitor - No open Synthetix positions found.")
                return False

            synthetix_funding_rate = self.synthetix.get_funding_rate(synthetix_position)

            size = float(synthetix_position['size'])
            is_long = size > 0
            is_profitable = (is_long and synthetix_funding_rate < 0) or (not is_long and synthetix_funding_rate > 0)

            return is_profitable
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error checking overall profitability for open positions: {e}")
            return False

    def is_position_delta_within_bounds(self) -> bool:
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
                asset_price = get_price_from_pyth(symbol)
            except Exception as e:
                logger.error(f"MasterPositionMonitor - Error retrieving asset price for {symbol}: {e}")
                return False

            synthetix_notional_value = float(synthetix_position['size']) * asset_price
            binance_notional_value = float(binance_position['size']) * asset_price

            synthetix_notional_value = synthetix_notional_value if synthetix_position['side'].upper() == 'LONG' else -synthetix_notional_value
            binance_notional_value = binance_notional_value if binance_position['side'].upper() == 'LONG' else -binance_notional_value

            total_notional_value = abs(synthetix_notional_value) + abs(binance_notional_value)
            delta_in_usd = abs(synthetix_notional_value - binance_notional_value)
            delta = (delta_in_usd / total_notional_value) if total_notional_value else 0

            logger.info(f'MasterPositionMonitor - Position delta calculated at {delta}. delta_in_usd: {delta_in_usd}, total_notional_value: {total_notional_value}, asset price: {asset_price}')

            return not delta > delta_bound
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Unexpected error in checking position delta: {e}")
            return False

    def is_funding_turning_against_trade_in_given_time(self, minuites: int) -> bool:
        try:
            synthetix_position = self.synthetix.get_open_position()
            is_long = synthetix_position['size'] > 0
            symbol = synthetix_position['symbol']

            market_data = MarketDirectory.get_market_params(symbol)
            if not market_data:
                raise ValueError(f"No market data available for symbol: {symbol}")

            market_summary = self.synthetix.client.perps.get_market_summary(market_data['market_id'])
            funding_rate = market_summary['current_funding_rate']
            velocity = market_summary['current_funding_velocity']

            future_blocks = minuites * 30
            predicted_funding_rate = funding_rate + (velocity * future_blocks / BLOCKS_PER_DAY_BASE)

            if (is_long and predicted_funding_rate < 0) or (not is_long and predicted_funding_rate > 0):
                return True 
            return False
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error checking if funding is turning against trade for {symbol}: {e}")
            return False




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
            time.sleep(25)
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
        exchanges = []
        is_liquidation_risk = self.check_liquidation_risk()
        is_profitable = self.check_profitability_for_open_position()
        is_delta_within_bounds = self.is_position_delta_within_bounds()
        is_funding_velocity_turning = self.is_synthetix_funding_turning_against_trade_in_given_time(30)

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

    def check_liquidation_risk(self, exchanges: list) -> bool:
        try:
            first_exchange = exchanges[0]
            second_exchange = exchanges[1]
            
            get_first_position_method = getattr(self, first_exchange.lower()).get_open_position
            get_second_position_method = getattr(self, second_exchange.lower()).get_open_position

            first_position = get_first_position_method()
            second_position = get_second_position_method()
        
            first_is_near_liquidation_method = getattr(self, first_exchange.lower()).is_near_liquidation_price(first_position)
            second_is_near_liquidation_method = getattr(self, second_exchange.lower()).is_near_liquidation_price(second_position)

            is_first_exchange_risk = first_is_near_liquidation_method()
            is_second_exchange_risk = second_is_near_liquidation_method()

            if is_first_exchange_risk or is_second_exchange_risk:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error while checking liquidation risk for positions on exchanges {exchanges}: {e}")
            return False

    def check_profitability_for_open_position(self, exchanges: list) -> bool:
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

    def is_position_delta_within_bounds(self, exchanges: list) -> bool:
        try:
            delta_bound = float(os.getenv('DELTA_BOUND'))
            first_exchange = exchanges[0]
            second_exchange = exchanges[1]
            
            get_first_position_method = getattr(self, first_exchange.lower()).get_open_position
            get_second_position_method = getattr(self, second_exchange.lower()).get_open_position

            first_position = get_first_position_method()
            second_position = get_second_position_method()

            if not first_position:
                logger.error(f"MasterPositionMonitor - Position for exchange {exchanges[0]} is missing when trying to calculate delta.")
                return False
            elif not second_position:
                logger.error(f"MasterPositionMonitor - Position for exchange {exchanges[1]}is missing when trying to calculate delta.")
                return False

            symbol = first_position['symbol']
            asset_price = get_price_from_pyth(symbol)

            first_notional_value = float(first_position['size']) * asset_price
            second_notional_value = float(second_position['size']) * asset_price

            first_notional_value = first_notional_value if first_notional_value['side'].upper() == 'LONG' else -first_notional_value
            second_notional_value = second_notional_value if second_notional_value['side'].upper() == 'LONG' else -second_notional_value

            total_notional_value = abs(first_notional_value) + abs(second_notional_value)
            delta_in_usd = abs(first_notional_value - second_notional_value)
            delta = (delta_in_usd / total_notional_value) if total_notional_value else 0

            logger.info(f'MasterPositionMonitor - Position delta calculated at {delta}. delta_in_usd: {delta_in_usd}, total_notional_value: {total_notional_value}, asset price: {asset_price}')

            return not delta > delta_bound
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Unexpected error in checking position delta: {e}")
            return False

    def is_synthetix_funding_turning_against_trade_in_given_time(self, mins: int) -> bool:
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

            future_blocks = mins * 30
            predicted_funding_rate = funding_rate + (velocity * future_blocks / BLOCKS_PER_DAY_BASE)

            if (is_long and predicted_funding_rate < 0) or (not is_long and predicted_funding_rate > 0):
                return True 
            return False
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error checking if funding is turning against trade for {symbol}: {e}")
            return False




from PositionMonitor.Synthetix.SynthetixPositionMonitor import SynthetixPositionMonitor
from PositionMonitor.Binance.BinancePositionMonitor import BinancePositionMonitor
from PositionMonitor.HMX.HMXPositionMonitor import HMXPositionMonitor
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.logger import *
from GlobalUtils.globalUtils import *
from GlobalUtils.MarketDirectories.SynthetixMarketDirectory import SynthetixMarketDirectory
from pubsub import pub
import threading
import sqlite3
import time

class MasterPositionMonitor():
    def __init__(self):
        self.synthetix = SynthetixPositionMonitor()
        self.binance = BinancePositionMonitor()
        self.hmx = HMXPositionMonitor()
        self.okx = OKXPositionMonitor()
        self.health_check_thread = None
        self.stop_health_check = threading.Event()
        
        pub.subscribe(self.on_position_opened, EventsDirectory.TRADE_LOGGED.value)
        pub.subscribe(self.on_position_closed, EventsDirectory.POSITION_CLOSED.value)

    def on_position_opened(self, position_data):
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            time.sleep(60)
            self.stop_health_check.clear()  
            self.health_check_thread = threading.Thread(target=self.start_health_check, daemon=True)
            self.health_check_thread.start()

    def on_position_closed(self, position_report):
        self.stop_health_check.set()

    def start_health_check(self):
        while not self.stop_health_check.is_set():
            self.position_health_check()
            time.sleep(15)

    def position_health_check(self):
        exchanges = self.get_exchanges_for_open_position()
        symbol = self.get_symbol_for_open_position()
        is_liquidation_risk = self.check_liquidation_risk(exchanges)
        is_profitable = self.check_profitability_for_open_positions(exchanges)
        is_delta_within_bounds = self.is_position_delta_within_bounds(exchanges)

        if 'Synthetix' in exchanges:
            is_funding_velocity_turning = self.is_synthetix_funding_turning_against_trade_in_given_time(15)

        if is_liquidation_risk:
            reason = PositionCloseReason.LIQUIDATION_RISK.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol=symbol, reason=reason, exchanges=exchanges)
        elif not is_profitable:
            reason = PositionCloseReason.NO_LONGER_PROFITABLE.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol=symbol, reason=reason, exchanges=exchanges)
        elif not is_delta_within_bounds:
            reason = PositionCloseReason.DELTA_ABOVE_BOUND.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol=symbol, reason=reason, exchanges=exchanges)
        elif is_funding_velocity_turning:
            reason = PositionCloseReason.FUNDING_TURNING_AGAINST_TRADE.value
            pub.sendMessage(EventsDirectory.CLOSE_POSITION_PAIR.value, symbol=symbol, reason=reason, exchanges=exchanges)
        else:
            logger.info('MasterPositionMonitor - no threat detected for open position')

    def check_liquidation_risk(self, exchanges: list) -> bool:
        try:
            first_exchange = str(exchanges[0])
            second_exchange = str(exchanges[1])
            
            position_one = get_open_position_for_exchange(first_exchange)
            position_two = get_open_position_for_exchange(second_exchange)

        
            is_first_exchange_risk: bool = getattr(self, first_exchange.lower()).is_near_liquidation_price(position_one)
            is_second_exchange_risk: bool = getattr(self, second_exchange.lower()).is_near_liquidation_price(position_two)

            if is_first_exchange_risk == None:
                logger.error(f'MasterPositionMonitor - is_near_liquidation_price return value for exchange {first_exchange} = None')

            if is_second_exchange_risk == None:
                logger.error(f'MasterPositionMonitor - is_near_liquidation_price return value for exchange {second_exchange} = None')

            logger.info(f'MasterPositionMonitor - Liquidation risk calculated as follows: {first_exchange} = {is_first_exchange_risk}, {second_exchange} = {is_second_exchange_risk}')

            if is_first_exchange_risk or is_second_exchange_risk:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error while checking liquidation risk for positions on exchanges {exchanges}: {e}")
            return False

    def check_profitability_for_open_positions(self, exchanges: list) -> bool:
        try:
            first_exchange = str(exchanges[0])
            second_exchange = str(exchanges[1])

            position_one = get_open_position_for_exchange(first_exchange)
            position_two = get_open_position_for_exchange(second_exchange)

            first_funding_rate = getattr(self, first_exchange.lower()).get_funding_rate(position_one)
            second_funding_rate = getattr(self, second_exchange.lower()).get_funding_rate(position_two)

            first_funding_rate = abs(first_funding_rate)
            second_funding_rate = abs(second_funding_rate)

            first_position_is_hedge = position_one['is_hedge'].lower() == 'True'
            second_position_is_hedge = position_two['is_hedge'].lower() == 'True'

            if first_position_is_hedge == True and first_funding_rate > second_funding_rate:
                return False
            elif second_position_is_hedge == True and second_funding_rate > first_funding_rate:
                return False
            else:
                return True

        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error checking overall profitability for open positions: {e}")
            return None

    def is_position_delta_within_bounds(self, exchanges: list) -> bool:
        try:
            delta_bound = float(os.getenv('DELTA_BOUND', '0.03'))
            positions = {}

            for exchange in exchanges:
                position = get_open_position_for_exchange(exchange)
                if not position:
                    logger.error(f"MasterPositionMonitor - Position for exchange {exchange} is missing when trying to calculate delta.")
                    return False
                notional_value = float(position['size_in_asset'])
                if position['side'].upper() == 'SHORT':
                    notional_value = -notional_value
                positions[exchange] = notional_value

            total_absolute_notional_value = sum(abs(value) for value in positions.values())
            absolute_delta = abs(positions[exchanges[0]] - positions[exchanges[1]])
            relative_delta = (absolute_delta / total_absolute_notional_value) if total_absolute_notional_value else 0


            return relative_delta - 1 <= delta_bound
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Unexpected error in checking position delta: {e}")
            return False



    def is_synthetix_funding_turning_against_trade_in_given_time(self, mins: int) -> bool:
        symbol = '' 
        try:
            synthetix_position = self.synthetix.get_open_position()
            if not synthetix_position:
                logger.error("MasterPositionMonitor - No open position found.")
                return None
            
            symbol = str(synthetix_position['symbol'])

            market_data = SynthetixMarketDirectory.get_market_params(symbol)
            if not market_data:
                logger.error(f"MasterPositionMonitor - No market data available for symbol: {symbol}")
                return None

            market_summary = self.synthetix.client.perps.get_market_summary(market_data['market_id'])
            funding_rate = float(market_summary['current_funding_rate'])
            velocity = float(market_summary['current_funding_velocity'])
            is_long = synthetix_position['size_in_asset'] > 0
            is_hedge = True if synthetix_position['is_hedge'] == 'True' else False

            future_blocks = mins * 30
            predicted_funding_rate = funding_rate + (velocity * future_blocks / BLOCKS_PER_DAY_BASE)

            if (is_long and not is_hedge and predicted_funding_rate < 0) or (not is_long and is_hedge and predicted_funding_rate > 0):
                return True
            return False

        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error checking if funding is turning against trade for {symbol}: {e}")
            return False


    def get_exchanges_for_open_position(self) -> list:
        try:
            with sqlite3.connect('trades.db') as conn:
                cursor = conn.cursor()
                query = """
                        SELECT DISTINCT exchange 
                        FROM trade_log 
                        WHERE open_close = 'Open';
                        """
                cursor.execute(query)
                exchanges = [exchange[0] for exchange in cursor.fetchall()]

                if len(exchanges) >= 2:
                    logger.info(f"MasterPositionMonitor - Found exchanges with open positions: {exchanges[:2]}")
                    return exchanges[:2] 
                else:
                    error_message = f"MasterPositionMonitor - Expected at least 2 exchanges with open positions but found {len(exchanges)}: {exchanges}"
                    logger.error(error_message)
                    return []
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error retrieving exchanges with open positions. Error: {e}")
            return None


    def get_symbol_for_open_position(self) -> str:
        try:
            with sqlite3.connect('trades.db') as conn:
                cursor = conn.cursor()
                query = """
                        SELECT symbol
                        FROM trade_log
                        WHERE open_close = 'Open'
                        LIMIT 1; 
                        """
                cursor.execute(query)
                symbol = cursor.fetchone() 

                if symbol:
                    return symbol[0]
                else:
                    logger.error("MasterPositionMonitor - No open position found.")
                    return None
        except Exception as e:
            logger.error(f"MasterPositionMonitor - Error retrieving symbol for open position. Error: {e}")
            return None

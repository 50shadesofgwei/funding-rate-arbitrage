import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

from PositionMonitor.Synthetix.SynthetixPositionMonitor import SynthetixPositionMonitor
from PositionMonitor.Binance.BinancePositionMonitor import BinancePositionMonitor
from pubsub import pub
from threading import Timer


class MasterPositionMonitor():
    def __init__(self):
        self.synthetix_order_details = None
        self.binance_order_details = None
        self.check_in_progress = False
        self.synthetix = SynthetixPositionMonitor()
        self.binance = BinancePositionMonitor()

        pub.subscribe(self.synthetix_position_opened, 'SynthetixPositionOpened')
        pub.subscribe(self.binance_position_opened, 'BinancePositionOpened')

    def synthetix_position_opened(self, event_object):
        synthetix_position = self.synthetix.get_position_object_from_event(event_object)
        self.synthetix_order_details = synthetix_position
        self.initiate_order_check()

    def binance_position_opened(self, event_object):
        binance_position = self.binance.get_position_object_from_event(event_object)
        self.binance_order_details = binance_position
        self.initiate_order_check()

    def initiate_order_check(self):
        if not self.check_in_progress:
            self.check_in_progress = True
            Timer(10, self.check_orders_and_handle).start()

    def check_orders_and_handle(self):
        if self.synthetix_order_details and self.binance_order_details:
            self.log_trade_to_database()
        else:
            self.send_error_event_and_close_orders()
        self.reset_state()

    def reset_state(self):
        self.synthetix_order_details = None
        self.binance_order_details = None
        self.check_in_progress = False

    def log_trade_to_database(self):
        # Log details to database here
        print("Both trades filled. Logging trade to database:", self.synthetix_order_details, self.binance_order_details)

    def send_error_event_and_close_orders(self):
        print("Error: Not both trades filled. Closing all orders.")
        # Trigger actions to close orders
        # self.synthetix.close_all_orders()
        # self.binance.close_all_orders()

        


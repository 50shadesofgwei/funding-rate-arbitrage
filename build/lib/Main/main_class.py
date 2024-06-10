from GlobalUtils.logger import *
from pubsub import pub
from APICaller.master.MasterCaller import MasterCaller
from MatchingEngine.MatchingEngine import matchingEngine
from MatchingEngine.profitabilityChecks.checkProfitability import ProfitabilityChecker
from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.MasterPositionMonitor import MasterPositionMonitor
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from PositionMonitor.TradeDatabase.TradeDatabase import TradeLogger
from GlobalUtils.globalUtils import *
from GlobalUtils.marketDirectory import MarketDirectory
import threading
import time

class Main:
    def __init__(self):
        setup_topics()
        self.caller = MasterCaller()
        self.matching_engine = matchingEngine()
        self.profitability_checker = ProfitabilityChecker()
        self.position_controller = MasterPositionController()
        self.position_controller.subscribe_to_events()
        self.position_monitor = MasterPositionMonitor()
        self.trade_logger = TradeLogger()
        MarketDirectory.initialize()
    
    def search_for_opportunities(self):
        try:
            funding_rates = self.caller.get_funding_rates()
            opportunities = self.matching_engine.find_delta_neutral_arbitrage_opportunities(funding_rates)
            opportunity = self.profitability_checker.find_most_profitable_opportunity(opportunities)
            if opportunity is not None:
                pub.sendMessage(EventsDirectory.OPPORTUNITY_FOUND.value, opportunity=opportunity)
            else:
                logger.error(f"MainClass - Error while searching for opportunity with object {opportunity}")

        except Exception as e:
            logger.error(f"MainClass - An error occurred during search_for_opportunities: {e}", exc_info=True)
            
    def start_search(self):
        while True:
            if not self.position_controller.is_already_position_open():
                self.search_for_opportunities()
            time.sleep(30) 


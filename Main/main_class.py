import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

import threading
import json
from pubsub import pub
from APICaller.master.MasterCaller import MasterCaller
from MatchingEngine.MatchingEngine import matchingEngine
from MatchingEngine.profitabilityChecks.checkProfitability import ProfitabilityChecker
from TxExecution.Master.MasterPositionController import MasterPositionController
from PositionMonitor.Master.Master import MasterPositionMonitor
from PositionMonitor.TradeDatabase.TradeDatabase import TradeLogger
import time

class Main:
    def __init__(self):
        self.caller = MasterCaller()
        self.matching_engine = matchingEngine()
        self.profitability_checker = ProfitabilityChecker()
        self.position_controller = MasterPositionController()
        self.position_monitor = MasterPositionMonitor()
        self.trade_logger = TradeLogger()
    
    def search_for_opportunities(self):
        funding_rates = self.caller.get_funding_rates()
        opportunities = self.matching_engine.find_delta_neutral_arbitrage_opportunities(funding_rates)
        best_opportunity = self.profitability_checker.find_most_profitable_opportunity(opportunities)
        pub.sendMessage('opportunity_found', opportunity = best_opportunity)

    
    def start_search(self):
        self.search_for_opportunities()
        # threading.Timer(10, self.start_search).start()

main = Main()
main.start_search()
time.sleep(10)
main.position_controller.cancel_all_trades()

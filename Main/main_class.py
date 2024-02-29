import sys
sys.path.append('/Users/jfeasby/SynthetixFundingRateArbitrage')

import threading
from APICaller.master.MasterCaller import MasterCaller
from MatchingEngine.MatchingEngine import matchingEngine
from MatchingEngine.profitabilityChecks.checkProfitability import ProfitabilityChecker

class Main:
    def __init__(self):
        self.caller = MasterCaller()
        self.matching_engine = matchingEngine()
        self.profitability_checker = ProfitabilityChecker()
    
    def search_for_opportunities(self):
        funding_rates = self.caller.get_funding_rates()
        opportunities = self.matching_engine.find_delta_neutral_arbitrage_opportunities(funding_rates)
        best_opportunity = self.profitability_checker.find_most_profitable_opportunity(opportunities)
        print(f"Best opportunity: {best_opportunity}")
    
    def start_search(self):
        self.search_for_opportunities()
        threading.Timer(30, self.start_search).start()

main = Main()
main.start_search()
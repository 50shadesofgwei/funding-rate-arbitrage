from GlobalUtils.logger import *
from pubsub import pub
from APICaller.master.MasterCaller import MasterCaller
from MatchingEngine.MatchingEngine import matchingEngine
from MatchingEngine.profitabilityChecks.checkProfitability import ProfitabilityChecker
from PositionMonitor.Master.MasterPositionMonitorUtils import *
from GlobalUtils.globalUtils import *
from GlobalUtils.MarketDirectories.SynthetixMarketDirectory import SynthetixMarketDirectory
from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory
import time
import json

class Demo:
    def __init__(self):
        setup_topics()
        self.caller = MasterCaller()
        self.matching_engine = matchingEngine()
        self.profitability_checker = ProfitabilityChecker()
        SynthetixMarketDirectory.initialize()
        GMXMarketDirectory.initialize()
    
    def search_for_opportunities(self):
        try:
            funding_rates = self.caller.get_funding_rates()
            opportunities = self.matching_engine.find_delta_neutral_arbitrage_opportunities(funding_rates)
            opportunities = self.profitability_checker.find_most_profitable_opportunity(opportunities, is_demo=True)

            with open('DEMO_opportunity_visualisations.json', 'w') as file:
                json.dump(opportunities, file, indent=4)

        except Exception as e:
            logger.error(f"MainClass - An error occurred during search_for_opportunities: {e}", exc_info=True)
            
    def start_search(self):
        while True:
            self.search_for_opportunities()
            time.sleep(30) 
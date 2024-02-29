from APICaller.master.MasterCaller import MasterCaller
from MatchingEngine.MatchingEngine import matchingEngine
from MatchingEngine.profitabilityChecks.checkProfitability import ProfitabilityChecker

class Main:
    def __init__(self):
        self.caller = MasterCaller()
        self.matching_engine = matchingEngine()
        self.profitability_checker = ProfitabilityChecker()

    
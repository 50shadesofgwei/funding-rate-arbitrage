from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from APICaller.GMX.GMXCallerUtils import *
set_paths()

class GMXCaller:
    def __init__(self):
        pass

    def get_funding_rates(self, symbols: list) -> dict:
        if not symbols:
            logger.error("GMXCaller - No symbols provided to fetch funding rates.")
            return None

        opportunities_raw = get_opportunities()

opportunities_raw = get_opportunities()
print(opportunities_raw)
        
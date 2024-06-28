from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger
from APICaller.GMX.GMXCallerUtils import *

class GMXCaller:
    def __init__(self):
        pass

    def get_funding_rates(self, symbols: list) -> dict:
        if not symbols:
            logger.error("GMXCaller - No symbols provided to fetch funding rates.")
            return None

        
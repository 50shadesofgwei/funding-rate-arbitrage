import logging
import inspect
from pubsub import pub
from functools import wraps

# Setup for the general application logger
logger = logging.getLogger(__name__)
app_handler = logging.FileHandler('app.log')
app_handler.setLevel(logging.INFO)
app_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_handler.setFormatter(app_formatter)
logger.addHandler(app_handler)
logger.setLevel(logging.INFO)

# Setup for the function tracker logger
function_logger = logging.getLogger("FunctionTracker")
function_tracker_handler = logging.FileHandler('functionTracker.log')
function_tracker_handler.setLevel(logging.DEBUG)
function_tracker_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
function_tracker_handler.setFormatter(function_tracker_formatter)
function_logger.addHandler(function_tracker_handler)
function_logger.setLevel(logging.DEBUG)


pub.setListenerExcHandler(logging.exception)

def setup_topics():
    pub.addTopicDefnProvider(TopicDefinitionProvider(), pub.TOPIC_TREE_FROM_CLASS)

class TopicDefinitionProvider:
    def getDefn(self, topicNameTuple):
        if topicNameTuple == ('opportunity_found',):
            return {'opportunity': "arbitrage opportunity found."}
        return None
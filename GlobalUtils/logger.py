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

def log_function_call(func):
    """
    A decorator to log function calls, making it easier to track the flow of the program,
    including the file name where the function is defined.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        module = inspect.getmodule(func)
        if module is not None and hasattr(module, '__file__'):
            file_name = module.__file__
            # Extract just the file name from the path for brevity
            file_name = file_name.split('/')[-1]
        else:
            file_name = 'Unknown'
        
        # Log entering and exiting messages with file name and function name
        function_logger.info(f"Entering {func.__name__} in {file_name}")
        result = func(*args, **kwargs)
        function_logger.info(f"Exiting {func.__name__} in {file_name}")
        return result
    return wrapper


pub.setListenerExcHandler(logging.exception)

def setup_topics():
    pub.addTopicDefnProvider(TopicDefinitionProvider(), pub.TOPIC_TREE_FROM_CLASS)

class TopicDefinitionProvider:
    def getDefn(self, topicNameTuple):
        if topicNameTuple == ('opportunity_found',):
            return {'opportunity': "arbitrage opportunity found."}
        return None
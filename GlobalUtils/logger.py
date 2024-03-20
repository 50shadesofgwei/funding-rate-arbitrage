import logging

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
    A decorator to log function calls, making it easier to track the flow of the program.
    """
    def wrapper(*args, **kwargs):
        function_logger.info(f"Entering {func.__name__}")
        result = func(*args, **kwargs)
        function_logger.info(f"Exiting {func.__name__}")
        return result
    return wrapper
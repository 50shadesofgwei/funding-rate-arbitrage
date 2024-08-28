from FlaskServer import create_app
from flask_socketio import SocketIO, emit
import logging
from GlobalUtils.logger import logger, app_formatter, setup_topics
from pubsub import pub
from GlobalUtils.globalUtils import EventsDirectory

(sio, app) = create_app()

# Setup topics for the application
setup_topics()

# Create PubSub Listeners for to redirect to SocketIO
def position_opened_to_socketio(position_data):
    sio.emit(EventsDirectory.POSITION_OPENED.value, position_data)

def position_closed_to_socketio(position_report):
    sio.emit(EventsDirectory.POSITION_CLOSED.value, position_report)

def close_all_positions_to_socketio():
    sio.emit(EventsDirectory.CLOSE_ALL_POSITIONS.value)

def close_position_pair_to_socketio(symbol, reason, exchanges):
    sio.emit(EventsDirectory.CLOSE_POSITION_PAIR.value, {"symbol": symbol, "reason": reason, "exchanges": exchanges})

def opportunity_found_to_socketio(opportunity):
    sio.emit(EventsDirectory.OPPORTUNITY_FOUND.value, opportunity)

def trade_logged_to_socketio(position_data):
    sio.emit(EventsDirectory.TRADE_LOGGED.value, position_data)

# Subscribe to all topics and forward to SocketIO
pub.subscribe(position_opened_to_socketio, EventsDirectory.POSITION_OPENED.value)
pub.subscribe(position_closed_to_socketio, EventsDirectory.POSITION_CLOSED.value)
pub.subscribe(close_all_positions_to_socketio, EventsDirectory.CLOSE_ALL_POSITIONS.value)
pub.subscribe(close_position_pair_to_socketio, EventsDirectory.CLOSE_POSITION_PAIR.value)
pub.subscribe(opportunity_found_to_socketio, EventsDirectory.OPPORTUNITY_FOUND.value)
pub.subscribe(trade_logged_to_socketio, EventsDirectory.TRADE_LOGGED.value)


# Custom handler for logging to the SocketIO
class SocketIOHandler(logging.Handler):
    def __init__(self, socketio):
        logging.Handler.__init__(self)
        self.socketio = socketio
    
    def emit(self, record):
        log_entry = self.format(record)
        self.socketio.emit('log', log_entry)

# Create and add SocketIOHandler to the logger
socketio_handler = SocketIOHandler(sio)
socketio_handler.setLevel(logging.INFO)
socketio_handler.setFormatter(app_formatter)
logger.addHandler(socketio_handler)


def run():
    sio.run(app)

if __name__ == "__main__":
    run()
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from PositionMonitor.TradeDatabase.TradeDatabase import TradeLogger
from FlaskServer.services import cli_commands, trade_routes, log_routes, settings
import os
from flask_socketio import SocketIO, emit

load_dotenv()

# Function will be for setting up configurations for the Flask app
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}) # TODO: Learn more about CORS 
    socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")
    app.trade_logger = TradeLogger()
    app.register_blueprint(cli_commands.api_routes)
    app.register_blueprint(trade_routes.routes)
    app.register_blueprint(log_routes.log_blueprint)
    app.register_blueprint(settings.settings_blueprint)

    if test_config is None:
        # Default configurations
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('FLASK_APP_SECRET_KEY'),
        )
    else:
        # Apply test configurations
        app.config.update(test_config)
    
    return socketio, app

# TODO: Write Route Unit Tests
    # - read advanced flask testing docs
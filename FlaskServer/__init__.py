from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from PositionMonitor.TradeDatabase.TradeDatabase import TradeLogger
import os
from flask_socketio import SocketIO
from FlaskServer.services import settings


load_dotenv()

# Function will be for setting up configurations for the Flask app
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, resources={r"/*": {"origins": "https://urchin-app-mwigp.ondigitalocean.app"}})
    socketio = SocketIO(app, cors_allowed_origins="https://urchin-app-mwigp.ondigitalocean.app")
    
    app.register_blueprint(settings.settings_blueprint)


    if test_config is None:
        # Default configurations
        app.config.from_mapping(
            SECRET_KEY=os.environ.get('FLASK_APP_SECRET_KEY'),
        )
    elif settings.is_env_valid():
        from FlaskServer.services import cli_commands, trade_routes, log_routes
        # Add Blueprints and routes
        app.trade_logger = TradeLogger()
        app.register_blueprint(cli_commands.api_routes)
        app.register_blueprint(trade_routes.routes)
        app.register_blueprint(log_routes.log_blueprint)
    else:
        # Apply test configurations
        app.config.update(test_config)
    
    return socketio, app

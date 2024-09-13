from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from PositionMonitor.TradeDatabase.TradeDatabase import TradeLogger
from flask_socketio import SocketIO
from FlaskServer.services import settings

load_dotenv()

# Function will be for setting up configurations for the Flask app
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, resources={r"/*": {"origins": "https://main.dmep2akgaq1vh.amplifyapp.com"}})
    socketio = SocketIO(app, cors_allowed_origins="https://main.dmep2akgaq1vh.amplifyapp.com")
    
    app.register_blueprint(settings.settings_blueprint)

    if settings.is_env_valid() :
        print("Using full configurations")
        try:
            from FlaskServer.services import cli_commands
            from FlaskServer.services import trade_routes
            from FlaskServer.services import log_routes
            # Add Blueprints and routes
            app.trade_logger = TradeLogger()
            app.register_blueprint(cli_commands.api_routes)
            app.register_blueprint(trade_routes.routes)
            app.register_blueprint(log_routes.log_blueprint)
        except Exception as e:
            print(f"Error: {e}")

    elif test_config is not None:
        # Apply test configurations
        app.config.update(test_config)
    
    return socketio, app

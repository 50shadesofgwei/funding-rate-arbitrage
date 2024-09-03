from flask import Blueprint, jsonify, request
from GlobalUtils.logger import logger
from typing import Dict, Any
from APICaller.master.MasterUtils import get_target_exchanges
from TxExecution.Master.MasterPositionController import MasterPositionController
import os, yaml
from dotenv import set_key, find_dotenv, get_key
settings_blueprint = Blueprint('settings', __name__, url_prefix='/settings')


@settings_blueprint.route('/find', methods=['GET'])
def find_settings():
    if os.access(path='./bot_settings.json', mode=os.R_OK) \
    and os.access(path='./bot_settings.json', mode=os.W_OK):
        bot_settings = get_bot_settings()
        if (bot_settings is None):
            return jsonify({"error": "Error getting settings"}), 500
        else:
            return jsonify(bot_settings), 200
    else:
        return jsonify('No file found!'), 404
    
    

@settings_blueprint.route('/bot-settings/get', methods=['GET'])
def get_bot_settings(): # TODO: Fix
    """
    Check if there is an existing `.env`:
    1. If not generate a .env file:
    
    2. Front-end will do an onboarding experience.
    """
    try:
        settings = {
            "max_allowable_percentage_away_from_liquidation_price": get_key('./.env', "MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE"),
            "trade_leverage": get_key('./.env', "TRADE_LEVERAGE"),
            "percentage_capital_per_trade": get_key('./.env', "PERCENTAGE_CAPITAL_PER_TRADE"),
            "default_trade_duration_hours": get_key('./.env', "DEFAULT_TRADE_DURATION_HOURS"),
            "default_trade_size_usd": get_key('./.env', "DEFAULT_TRADE_SIZE_USD")
        }
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return None

@settings_blueprint.route('/bot-settings/set', methods=['POST']) # TODO: Fix
def set_bot_settings(body):
    try:
        if _check_bot_settings(body):
            for key, value in body.items():
                set_key(find_dotenv(), str(key).upper(), value)
            return jsonify({"success": "Settings updated"}), 200
    except Exception as e:
        logger.error(f"Error setting settings: {e}")
        return False
    
@settings_blueprint.route('/exchange-settings/set', methods=['POST'])
def set_exchange_settings(): # TODO: Fix
    try:
        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({"error": "Invalid Request bad body"}), 400
        if "exchange" in data and "settings" in data:
            exchange = data["exchange"]
            settings = data["settings"]
            if _check_exchange_settings(settings):
                for key, value in settings.items():
                    set_key(find_dotenv(), key, value)
                return jsonify({"success": "Settings updated"}), 200
            else:
                return jsonify({"error": "Invalid settings"}), 400
        else:
            return jsonify({"error": "Invalid Request"}), 400
    except Exception as error:
        return jsonify(error), 500

@settings_blueprint.route('/wallet-settings/get', methods=['GET'])
def get_wallet_settings(): # TODO: Fix
    """
    Get Wallet Settings
    """
    wallet_settings = {}
    wallet_settings['address'] = get_key(find_dotenv(), "ADDRESS")
    wallet_settings['base_provider_rpc'] = get_key(find_dotenv(), "BASE_PROVIDER_RPC")
    wallet_settings['arbitrum_provider_rpc'] = get_key(find_dotenv(), "ARBITRUM_PROVIDER_RPC")
    wallet_settings['chain_id_base'] = get_key(find_dotenv(), "CHAIN_ID_BASE")
    return jsonify(wallet_settings), 200

@settings_blueprint.route('/wallet-settings/set', methods=['POST'])
def set_wallet_settings():
    """
    Set Wallet Settings
    """
    data: Dict[str, Any] = request.get_json()
    if not data:
        return jsonify({"error": "Invalid Request bad body"}), 400
    if _check_wallet_settings(data):
        address = data["wallet_address"]
        private_key = data["private_key"]
        set_key(find_dotenv(), "ADDRESS", address)
        set_key(find_dotenv(), "PRIVATE_KEY", private_key)
        return jsonify({"success": "Wallet Settings updated"}), 200
    else:
        return jsonify({"error": "Invalid Request"}), 400

@settings_blueprint.route('/collateral/<exchange>')
def get_deployed_collateral(exchange: str):
    """
        Get Collateral in each Perps Market
    """
    target_exchanges = get_target_exchanges()
    if exchange in target_exchanges:
        master_position_caller = MasterPositionController()
        collateral: float = master_position_caller.get_available_collateral_for_exchange(exchange=exchange)
        return jsonify(collateral), 200
    else:
        return jsonify("Invalid Exchange!"), 400
    
####################
#  Settings f(x)   #
####################
def _check_bot_settings(bot_settings: dict) -> bool: # TODO: Fix
    try:
        settings = bot_settings['settings']
        if (settings['max_allowable_percentage_away_from_liquidation_price'] < 5)  or (settings['max_allowable_percentage_away_from_liquidation_price'] > 30):
            logger.error("GlobalUtils - MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE must be between 5 and 30")
            return False
        if (settings['trade_leverage'] > 10 ):
            logger.error("GlobalUtils - TRADE_LEVERAGE must be greater than 10")
            return False
        if (settings['percentage_capital_per_trade'] < 0 or settings['percentage_capital_per_trade'] > 100):
            logger.error("GlobalUtils - PERCENTAGE_CAPITAL_PER_TRADE must be between 0 and 100")
            return False
        if (settings['default_trade_duration_hours'] < 6 or settings['default_trade_duration_hours'] > 24):
            logger.error("GlobalUtils - DEFAULT_TRADE_DURATION_HOURS must be greater than 0")
            return False
        if (settings['default_trade_size_usd'] < 50 or settings['default_trade_size_usd'] > 1_000_000):
            logger.error("GlobalUtils - DEFAULT_TRADE_SIZE_USD must be between 50 and 1,000,000")
            return False
    except KeyError:
        logger.error("KeyError: Check whether all required settings are present")
        return False
    else:
        return True

def _check_exchange_settings(exchange_settings: dict) -> bool: # TODO: Fix
    try:
        for key, value in exchange_settings.items():
            if key == "api_key" or key == "api_secret":
                if len(value) < 10:
                    return False
    except Exception as e:
        logger.error(f"Error checking exchange settings: {e}")
        return False
    return True

def _check_wallet_settings(wallet_settings: dict) -> bool: # TODO: Fix
    try:
        if len(wallet_settings["wallet_address"]) < 10 or len(wallet_settings["wallet_private_key"]) < 10:
            return False
    except Exception as e:
        logger.error(f"Error checking wallet settings: {e}")
        return False
    return True

def _check_gmx_config_file():
    '''
        Called before running the bot
    '''
    if find_dotenv('config.yaml') == '':
        logger.error("GlobalUtils - GMX config file not found")
        return False
    else:
        try:
            _create_gmx_config_file()
            return True
        except Exception as e:
            logger.error(f"GlobalUtils - Error creating GMX config file: {e}")
            return False

def _create_gmx_config_file():
    yaml_config = {}
    yaml_config['rpcs'] = {
        'arbitrum': get_key(find_dotenv(), "ARBITRUM_PROVIDER_RPC"),
        'avalanche': 'api.avax-test.network',
    }
    yaml_config['chain_ids'] = {
        'arbitrum': 42161,
        'avalanche': '43113',
    }
    with open('config.yaml', 'w') as file:
        yaml.dump(yaml_config, file)
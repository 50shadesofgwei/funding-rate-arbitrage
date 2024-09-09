from flask import Blueprint, jsonify, request, after_this_request
from GlobalUtils.logger import logger
from typing import Dict, Any
from APICaller.master.MasterUtils import get_target_exchanges
import os, yaml
from dotenv import set_key, find_dotenv, get_key, dotenv_values
import subprocess, sys

settings_blueprint = Blueprint('settings', __name__, url_prefix='/settings')


@settings_blueprint.route('/find', methods=['GET'])
def find_settings():
    if is_env_valid():
        return jsonify("valid"), 200
    else:
        return jsonify({"error": "Error getting settings"}), 404
    

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

@settings_blueprint.route('/complete-onboarding', methods=['POST'])
def complete_onboarding():
    try:
        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({"error": "Invalid Request: bad body"}), 400
        

        # Set Wallet Settings
        wallet_result = set_wallet_settings(data['walletSettings'])
        try:
            if wallet_result['status'] != 'success':
                return jsonify(wallet_result), 400
        except KeyError as e:
            return jsonify({"error": str(e)}), 400
        
        # Set Exchange Settings
        exchange_result = set_exchange_settings(data['exchangeSettings'])
        try:
            if exchange_result['status'] != 'success':
                return jsonify(exchange_result), 400
        except KeyError as e:
            return jsonify({"error": str(e)}), 400

        # Set Bot Settings
        bot_result = set_bot_settings(data['botSettings'])
        try:
            if bot_result['status'] != 'success':
                return jsonify(bot_result), 400
        except KeyError as e:
            return jsonify({"error": str(e)}), 400

        # If all settings were successfully updated
        return jsonify({
            "status": "success",
            "message": "Onboarding completed successfully",
            "wallet": wallet_result['message'],
            "exchange": exchange_result['message'],
            "bot": bot_result['message']
        }), 200

    except Exception as error:
        return jsonify({"error": str(error)}), 500

@settings_blueprint.route('/wallet-settings/set', methods=['POST'])
def set_wallet_settings_route():
    try:
        settings = request.json
        set_wallet_settings(settings)
        return jsonify({"message": "Wallet settings updated successfully"}), 200
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@settings_blueprint.route('/exchange-settings/set', methods=['POST'])
def set_exchange_settings_route():
    try:
        settings = request.json
        response = set_exchange_settings(settings)

        if response['status'] == 'success':
            return jsonify({"message": "Exchange settings updated successfully"}), 200
        else:
            return jsonify(response), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 500

@settings_blueprint.route('/bot-settings/set', methods=['POST'])
def set_bot_settings_route():
    try:
        settings = request.json
        response = set_bot_settings(settings)

        if response['status'] == 'success':
            return jsonify({"message": "Bot settings updated successfully"}), 200
        else:
            return jsonify(response), 400
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@settings_blueprint.route('/restart-bot', methods=['POST'])
def restart_bot():
    subprocess.Popen([sys.executable, sys.argv])
    os._exit(0)

####################
#  Settings f(x)   #
####################
def is_env_valid() -> bool:
    try:
        if os.access(path='./.env', mode=os.R_OK) \
        and os.access(path='./.env', mode=os.W_OK):
            env_settings = dotenv_values('.env')
            if _check_wallet_settings(env_settings):
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
        return False


def _check_bot_settings(bot_settings: dict) -> bool: # TODO: Fix
    try:
        settings = bot_settings
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

def _check_wallet_settings(wallet_settings: dict) -> bool: # TODO: Fix make tests better
    try:
        if len(wallet_settings["wallet_address"]) < 10 or len(wallet_settings["wallet_private_key"]) < 10:
            return False
        if len(wallet_settings["base_provider_rpc"]) < 10 or len(wallet_settings["arbitrum_provider_rpc"]) < 10:
            return False
        if len(wallet_settings["chain_id_base"]) < 1:
            return False
        if len(wallet_settings["chain_id_arbitrum"]) < 1:
            return False
    except Exception as e:
        logger.error(f"Error checking wallet settings: {e}")
        return False
    return True

def _check_gmx_config_file():
    '''
        Called before running the bot
    '''
    if os.access(path='config.yaml', mode=os.R_OK) and os.access(path='config.yaml', mode=os.W_OK):
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
        'arbitrum': get_key(find_dotenv(), "CHAIN_ID_BASE"),
        'avalanche': '43113',
    }
    with open('config.yaml', 'w') as file:
        yaml.dump(yaml_config, file)

def set_wallet_settings(data: Dict[str, Any]):
    try:
        if not data or not isinstance(data, dict):
            return {"error": "Invalid request body"}

        # Validate required fields
        required_fields = ['address', 'arbitrum_rpc', 'network']
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}

        # Update .env file
        set_key('.env', 'ADDRESS', data['address'])
        set_key('.env', 'ARBITRUM_PROVIDER_RPC', data['arbitrum_rpc'])
        set_key('.env', 'CHAIN_ID_BASE', str(data['network']))

        return {
            "status": "success",
            "message": "Wallet settings updated successfully"
        }

    except Exception as error:
        return {"error": str(error)}

def set_exchange_settings(data: Dict[str, Any]):
    try:
        if not data or not isinstance(data, dict):
            return {"error": "Invalid request body"}

        # Validate required fields
        required_exchanges = ['bybit', 'binance']
        for exchange in required_exchanges:
            if exchange not in data:
                return {"error": f"Missing settings for {exchange}"}
            if not all(key in data[exchange] for key in ['apiKey', 'apiSecret', 'enabled']):
                return {"error": f"Invalid settings for {exchange}"}

        # Update .env file
        for exchange in required_exchanges:
            set_key('.env', f'{exchange.upper()}_API_KEY', data[exchange]['apiKey'])
            set_key('.env', f'{exchange.upper()}_API_SECRET', data[exchange]['apiSecret'])
            set_key('.env', f'{exchange.upper()}_ENABLED', str(data[exchange]['enabled']).lower())

        return {
            "status": "success",
            "message": "Exchange settings updated successfully"
        }

    except Exception as error:
        return {"error": str(error)}

def set_bot_settings(data: Dict[str, Any]):
    try:
        if not data or not isinstance(data, dict):
            return {"error": "Invalid request body"}

        # Validate required fields
        required_fields = [
            'max_allowable_percentage_away_from_liquidation_price',
            'trade_leverage',
            'percentage_capital_per_trade',
            'default_trade_duration_hours',
            'default_trade_size_usd'
        ]
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}
        if not _check_bot_settings(data):
            return {"error": "Invalid bot settings check upper and lower bounds"}
        # Update .env file
        for field in required_fields:
            env_key = field.upper()
            set_key('.env', env_key, str(data[field]))

        return {
            "status": "success",
            "message": "Bot settings updated successfully"
        }

    except Exception as error:
        return {"error": str(error)}


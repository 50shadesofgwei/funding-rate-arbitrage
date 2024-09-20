from flask import Blueprint, jsonify, request
from GlobalUtils.logger import logger
from typing import Dict, Any
import os, yaml
from dotenv import set_key, get_key, dotenv_values, load_dotenv
import subprocess
import web3, requests, time, re
import sys
settings_blueprint = Blueprint('settings', __name__, url_prefix='/settings')

@settings_blueprint.route('/find', methods=['GET'])
def find_settings():
    load_dotenv()
    if is_env_valid():
        return jsonify("valid"), 200
    else:
        return jsonify({"error": "Error getting settings"}), 404
    

@settings_blueprint.route('/bot-settings/get', methods=['GET'])
def get_bot_settings():
    try:
        settings = {
            "max_allowable_percentage_away_from_liquidation_price": int(get_key('./.env', "MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE")),
            "trade_leverage": int(get_key('./.env', "TRADE_LEVERAGE")),
            "percentage_capital_per_trade": int(get_key('./.env', "PERCENTAGE_CAPITAL_PER_TRADE")),
            "default_trade_duration_hours": int(get_key('./.env', "DEFAULT_TRADE_DURATION_HOURS")),
            "default_trade_size_usd": int(get_key('./.env', "DEFAULT_TRADE_SIZE_USD"))
        }
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return None


@settings_blueprint.route('/wallet-settings/get', methods=['GET'])
def get_wallet_settings():
    """
        Get Wallet Settings
    """
    wallet_settings = {}
    wallet_settings['address'] = get_key('./.env', "ADDRESS")
    wallet_settings['base_provider_rpc'] = get_key('./.env', "BASE_PROVIDER_RPC")
    wallet_settings['arbitrum_provider_rpc'] = get_key('./.env', "ARBITRUM_PROVIDER_RPC")
    wallet_settings['chain_id_base'] = get_key('./.env', "CHAIN_ID_BASE")
    return jsonify(wallet_settings), 200

@settings_blueprint.route('/exchange-settings/get', methods=['GET'])
def get_exchange_settings():
    """
        Get ByBit Exchange Settings
    """
    exchange_settings = {}
    exchange_settings['bybit'] = {
        "apiKey": get_key('./.env', "BYBIT_API_KEY"),
        "apiSecret": get_key('./.env', "BYBIT_API_SECRET"),
    }
    return jsonify(exchange_settings), 200

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

        # Update GMX Config File with new settings
        _create_gmx_config_file()

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
    try:
        if sys.platform.startswith('win'):
            # Windows-specific code
            subprocess.Popen([f"./venv/Scripts/project-run-ui.exe"])
        elif sys.platform.startswith('darwin'):
            # macOS-specific code
            subprocess.Popen([f"./venv/bin/project-run-ui"])
        else:
            # Linux or other Unix-like systems
            subprocess.Popen([f"./venv/bin/project-run-ui"])
        os._exit(0)
        return jsonify({"status": "Bot restarted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


###################
#  Settings f(x)  #
###################
def is_env_valid() -> bool:
    try:
        if os.access(path='./.env', mode=os.R_OK) \
        and os.access(path='./.env', mode=os.W_OK):
            env_settings = dotenv_values('.env')
            if _check_wallet_settings({
                "wallet_address": env_settings["ADDRESS"],
                "base_provider_rpc": env_settings["BASE_PROVIDER_RPC"],
                "arbitrum_provider_rpc": env_settings["ARBITRUM_PROVIDER_RPC"],
                "chain_id_base": env_settings["CHAIN_ID_BASE"],
                "private_key": env_settings["PRIVATE_KEY"]
            }):
                if _check_exchange_settings({
                    "bybit": {
                        "apiKey": env_settings["BYBIT_API_KEY"],
                        "apiSecret": env_settings["BYBIT_API_SECRET"],
                        "enabled": env_settings["BYBIT_ENABLED"]
                    },
                    "binance": {
                        "apiKey": env_settings["BINANCE_API_KEY"],
                        "apiSecret": env_settings["BINANCE_API_SECRET"],
                        "enabled": env_settings["BINANCE_ENABLED"]
                    }
                }):
                    if _check_bot_settings(bot_settings={
                        "max_allowable_percentage_away_from_liquidation_price": int(env_settings["MAX_ALLOWABLE_PERCENTAGE_AWAY_FROM_LIQUIDATION_PRICE"]),
                        "trade_leverage": int(env_settings["TRADE_LEVERAGE"]),
                        "percentage_capital_per_trade": int(env_settings["PERCENTAGE_CAPITAL_PER_TRADE"]),
                        "default_trade_duration_hours": int(env_settings["DEFAULT_TRADE_DURATION_HOURS"]),
                        "default_trade_size_usd": int(env_settings["DEFAULT_TRADE_SIZE_USD"])
                    }):
                        return True
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


def _check_exchange_settings(exchange_settings: dict) -> bool:
    """Currently only checks ByBit settings"""
    try:
        if exchange_settings["bybit"]["enabled"] == "true":
            if len(exchange_settings["bybit"]["apiKey"]) < 10 or len(exchange_settings["bybit"]["apiSecret"]) < 15:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Error checking exchange settings: {e}")
        return False
    return True


def _check_wallet_settings(wallet_settings: dict) -> bool:
    try:
        if not web3.Web3.is_address(wallet_settings["wallet_address"]) or not re.match(r'^(0x)?[0-9a-fA-F]{64}$', wallet_settings["private_key"]):
            return False
        if not _check_rpc_validity(wallet_settings["arbitrum_provider_rpc"]) or not _check_rpc_validity(wallet_settings["base_provider_rpc"]):
            return False
        if int(wallet_settings["chain_id_base"]) != 42161 and int(wallet_settings["chain_id_base"]) != 421614:
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
        'arbitrum': get_key('./.env', "ARBITRUM_PROVIDER_RPC"),
        'avalanche': 'api.avax-test.network',
    }
    yaml_config['chain_ids'] = {
        'arbitrum': int(get_key('./.env', "CHAIN_ID_BASE")),
        'avalanche': 43113,
    }

    yaml_config['private_key'] = get_key('./.env', "PRIVATE_KEY")
    yaml_config['user_wallet_address'] = get_key('./.env', "ADDRESS")

    with open('config.yaml', 'w') as file:
        yaml.dump(yaml_config, file)


def _check_rpc_validity(rpc_url, polling_interval=0.5, max_retries=3):
    """
    Check the validity of an RPC endpoint by polling it.
    
    :param rpc_url: The URL of the RPC endpoint to check
    :param polling_interval: Time in seconds between each poll attempt
    :param max_retries: Maximum number of retry attempts before giving up
    :return: True if the RPC is valid, False otherwise
    """
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Prepare a simple JSON-RPC request
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }

            # Send the request to the RPC endpoint
            response = requests.post(rpc_url, json=payload, timeout=10)

            # Check if the response is valid
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return True
                else:
                    print(f"Invalid RPC response: {result}")
            else:
                print(f"Invalid response status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to RPC: {e}")

        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying in {polling_interval} seconds...")
            time.sleep(polling_interval)

    print(f"Max retries ({max_retries}) reached. RPC endpoint is not valid.")
    return False


def set_wallet_settings(data: Dict[str, Any]):
    try:
        if not data or not isinstance(data, dict):
            return {"error": "Invalid request body"}

        # Validate required fields
        required_fields = ['address', 'arbitrum_rpc', 'base_rpc', 'network']
        if not all(field in data for field in required_fields):
            return {"error": "Missing required fields"}

        # Update .env file
        set_key('.env', 'ADDRESS', data['address'], quote_mode='never')
        set_key('.env', 'ARBITRUM_PROVIDER_RPC', data['arbitrum_rpc'], quote_mode='never')
        set_key('.env', 'BASE_PROVIDER_RPC', data['base_rpc'], quote_mode='never')
        set_key('.env', 'CHAIN_ID_BASE', str(data['network']), quote_mode='never')

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
            set_key('.env', f'{exchange.upper()}_API_KEY', data[exchange]['apiKey'], quote_mode='never')
            set_key('.env', f'{exchange.upper()}_API_SECRET', data[exchange]['apiSecret'], quote_mode='never')
            set_key('.env', f'{exchange.upper()}_ENABLED', str(data[exchange]['enabled']).lower(), quote_mode='never')

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
            set_key('.env', env_key, str(data[field]), quote_mode='never')

        return {
            "status": "success",
            "message": "Bot settings updated successfully"
        }

    except Exception as error:
        return {"error": str(error)}


def get_bot_status():    
    if is_env_valid():
        status = get_key('./.env', "BOT_STATUS")
        return jsonify({"status": status}), 200
    return jsonify({"error": "Invalid Settings Configuration"}), 500


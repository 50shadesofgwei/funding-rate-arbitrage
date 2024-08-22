from flask import Blueprint, jsonify, request
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import \
    set_bot_settings, get_bot_settings, \
    set_binance_config, set_hmx_config, set_okx_config, set_synthetix_config, set_bybit_config

from typing import Dict, Any
from APICaller.master.MasterUtils import get_target_exchanges
from TxExecution.Master.MasterPositionController import MasterPositionController
import os

# TODO: File-based storage for Version 1

settings_blueprint = Blueprint('settings', __name__, url_prefix='/settings')

@settings_blueprint.route('/get', methods=['GET'])
def get_settings():
    """
    Check if there is an existing `bot_settings.json`:
    1. If not generates bot_settings file:
    
    2. Front-end will do an onboarding experience.
    """
    if os.access(path='./bot_settings.json', mode=os.R_OK) \
    and os.access(path='./bot_settings.json', mode=os.W_OK):
        bot_settings = get_bot_settings()
        if (bot_settings is None):
            return jsonify({"error": "Error getting settings"}), 500
        else:
            return jsonify(bot_settings), 200
    else:
        return jsonify('No file found!'), 500
        # Invoke on-boarding experience to the user
    

@settings_blueprint.route('/set', methods=['POST'])
def set_settings():
    body = request.get_json()
    if set_bot_settings(body):
        return jsonify({"message": "Settings updated"})
    else:
        return jsonify({"error": "Invalid settings options"}), 400

@settings_blueprint.route('/set/exchange-env', methods=['POST'])
def set_exchange_config():
    try:

        data: Dict[str, Any] = request.get_json()
        if not data:
            return jsonify({"error": "Invalid Request bad body"}), 400
        
        results = {}

        if "synthetix" in data:
            # Extract api-keys etc
            results["synthetix"] = set_synthetix_config()
        
        if "binance" in data:
            binance_data = data["binance"]
            if "api_key" in binance_data and "api_secret" in binance_data:
                results["binance"] = set_binance_config(binance_data["api_key"], binance_data["api_secret"])
            else:
                results["binance"] = {"error": "Missing API key or secret"}

        if "bybit" in data:
            results["bybit"] = set_bybit_config()

        if "hmx" in data:
            # Config yaml file
            results["hmx"] = set_hmx_config()

        if "okx" in data:
            results["okx"] = set_okx_config()
    except Exception as error:
        return jsonify(error), 500
    else:
        return jsonify({"success"}), 200

"""
    Get Collateral in each Perps Market
"""
@settings_blueprint.route('/collateral/<exchange>')
def get_deployed_collateral(exchange: str):
    target_exchanges = get_target_exchanges()
    if exchange in target_exchanges:
        master_position_caller = MasterPositionController()
        collateral: float = master_position_caller.get_available_collateral_for_exchange(exchange=exchange)
        return jsonify(collateral), 200
    else:
        return jsonify("Invalid Exchange!"), 400
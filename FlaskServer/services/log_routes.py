from flask import Blueprint, jsonify, request
from GlobalUtils.logger import logger
from GlobalUtils.globalUtils import get_app_logs, clear_logs

log_blueprint = Blueprint('log_routes', __name__, url_prefix='/logs')

@log_blueprint.route('/app', methods=['GET'])
def get_logs():
    logs = get_app_logs()
    if type(logs) is not bool:
        return jsonify({"logs": get_app_logs()})
    else:
        return jsonify({"error": "Error getting logs"}), 500

@log_blueprint.route('/function', methods=['GET'])
def get_function_logs():
    with open("function.log", "r") as f:
        logs = f.readlines()
    return jsonify(logs)

@log_blueprint.route('/clear', methods=['POST'])
def clear():
    if clear_logs():
        return jsonify({"status": "Logs cleared"})
    else:
        return jsonify({"error": "Can't clear logs"}), 500


@log_blueprint.route('/log/<message>', methods=['POST'])
def log(message):
    logger.info("FlaskServer.services.log_routes - " + message)
    return jsonify({"status": "Logged"}), 200
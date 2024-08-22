from flask import Blueprint, jsonify, request
from GlobalUtils.logger import logger, function_logger
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

@log_blueprint.route('/function_log', methods=['POST'])
def add_function_log():
    data = request.json
    message = data.get('message', '')
    function_logger.info(message)
    return jsonify({'message': 'Function log added successfully'}), 201


# TODO: Make the log route output a JSON object instead of string
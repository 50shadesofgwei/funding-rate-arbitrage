from flask import Blueprint, jsonify, request
from Main.main_class import Main
from Main.main_class_demo import Demo
from TxExecution.Master.MasterPositionController import MasterPositionController
import threading
import json

api_routes = Blueprint('api_routes', __name__)

bot_instance = None
bot_thread = None

@api_routes.route('/run', methods=['POST'])
def run():
    global bot_instance, bot_thread
    if not bot_instance or not bot_thread or not bot_thread.is_alive():
        bot_instance = Main()
        bot_thread = threading.Thread(target=bot_instance.start_search)
        bot_thread.start()
        return jsonify({"status": "Bot started"}), 200
    else:
        return jsonify({"status": "Bot already running"}), 200

@api_routes.route('/stop', methods=['POST'])
def stop():
    global bot_instance, bot_thread
    if bot_instance and bot_thread and bot_thread.is_alive():
        if bot_instance.is_executing_trade:
            return jsonify({"status": "Bot is currently executing a trade. Try again later"}), 403
        else:
            bot_instance.bot_running = False
            bot_thread.join()  # Wait for the thread to finish
            return jsonify({"status": "Bot stopped successfully"}), 200
    else:
        return jsonify({"status": "Bot is not running"}), 400


'''Main.run:demo'''
@api_routes.route('/demo', methods=['POST'])
def demo(): # TODO:  Check
    '''Main.run:demo'''
    global bot_running, bot_instance
    if bot_running and bot_instance:
        if bot_instance.is_paused():
            # Run the demo
            demo_instance = main_run.Demo()
            demo_instance.search_for_opportunities()
            return jsonify({"status": "Running demo..."}), 200
    else:
        print("Pausing bot...")
        return jsonify({"status": "Running demo..."})


# TxExecution.Master.run:main
@api_routes.route('/close-position-pair', methods=['POST'])
def close_position(): # TODO: Check
    global bot_running, bot_instance
    if bot_running and bot_instance:
        data = request.json
        symbol = data.get('symbol')
        reason = data.get('reason')
        exchanges = data.get('exchanges')

        if not all([symbol, reason, exchanges]):
            return jsonify({"status": "Missing required parameters"}), 400
        
        if not bot_instance.position_controller.is_executing_trade:
            bot_instance.position_controller.close_position_pair(symbol, reason, exchanges)
            return jsonify({"status": "Position pair closing initiated..."}), 200
        else:
            return jsonify({"status": "Cannot close position pair, bot is executing a trade try again in a bit."}), 400
    else:
        return jsonify({"status": "Bot is not running"}), 400

@api_routes.route('/status', methods=['GET'])
def status():
    global bot_running
    return jsonify({"status": "running" if bot_running else "stopped"})

@api_routes.route('/collateral/<exchange>', methods=['GET'])
def get_collateral(exchange):
    try:
        collateral: float = MasterPositionController.get_available_collateral_for_exchange(exchange)
        return jsonify(collateral), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

######################
# Internal Functions #
######################
def _get_demo_opportunities():
    try:
        with open('DEMO_opportunity_visualisations.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}
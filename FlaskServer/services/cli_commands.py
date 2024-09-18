from flask import Blueprint, jsonify, request
import pubsub.pub
from Main.main_class import Main
from Main.main_class_demo import Demo
from TxExecution.Master.MasterPositionController import MasterPositionController
import threading
import json
import pubsub
from GlobalUtils.logger import *
import sys, os, subprocess
api_routes = Blueprint('api_routes', __name__)

# Bot Related variables
bot_instance = Main()
bot_thread = None
is_running = False

# Demo Related variables
demo_instance = Demo()
demo_running = False


@api_routes.route('/run', methods=['POST'])
def run():
    global bot_instance, bot_thread, is_running
    try:
        if not bot_instance.bot_running:
            if bot_thread:
                if bot_thread.is_alive():
                    print("Bot thread is still alive!")
                    return jsonify({"status": "Bot thread is still alive!"}), 403
            else:
                bot_thread = threading.Thread(target=bot_instance.start_search)
                bot_thread.start()
                is_running = True
                return jsonify({"status": "Bot started"}), 200
        else:
            print("Bot already running!")
            return jsonify({"status": "Bot already running"}), 403
    except Exception as e:
        logger.error(f"FlaskServer - Threading problem: {e}")
        return jsonify({"status": str(e)}), 500
@api_routes.route('/stop', methods=['POST'])
def stop():
    global bot_instance, bot_thread, is_running
    if bot_instance:
        if bot_instance.bot_running:
            if not bot_instance.is_executing_trade:
                bot_instance.bot_running = False
                bot_thread.join()  # Wait for the thread to finish
                is_running = False
                logger.info("Bot stopped successfully")
                return jsonify({"status": "Bot stopped successfully"}), 200
            else:
                return jsonify({"status": "Cannot stop the bot, it is executing a trade"}), 403
        else:
            return jsonify({"status": "Bot is not running"}), 403
    else:
        return jsonify({"status": "Bot is not running"}), 403

@api_routes.route('/restart-bot', methods=['POST'])
def restart_bot():
    try:
        global bot_instance, is_running
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

'''Main.run:demo'''
@api_routes.route('/demo', methods=['POST'])
def demo(): # TODO: Check
    '''Main.run:demo'''
    global bot_instance
    if bot_instance:
        if bot_instance.bot_running:
            return jsonify({"status": "Temporarily stop the bot to run this function."}), 403
        else:
            # Run the demo
            demo_instance = Demo()
            demo_instance.search_for_opportunities()
            pubsub.pub.sendMessage("demo_opportunity")
            return jsonify({"status": "Demo ran"}), 200
    else:
        demo_instance = Demo()
        demo_instance.search_for_opportunities()
        pubsub.pub.sendMessage("demo_opportunity")
        return jsonify({"status": "Demo ran"}), 200


# TxExecution.Master.run:main
@api_routes.route('/close-position-pair', methods=['POST'])
def close_position(): # TODO: Check
    global is_running, bot_instance
    if is_running:
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
    global is_running
    return jsonify({"status": "running" if is_running else "stopped"})

@api_routes.route('/collateral/<exchange>', methods=['GET'])
def get_collateral(exchange):
    try:
        collateral: float = execution_instance.get_available_collateral_for_exchange(exchange=exchange)
        return jsonify(collateral), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    

######################
# Internal Functions #
######################
@api_routes.route('/get-demo')
def get_demo_opportunities():
    try:
        with open('DEMO_opportunity_visualisations.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


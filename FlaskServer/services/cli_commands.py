from flask import Blueprint, jsonify
import Main.run as main_run
from pubsub import pub
from TxExecution.Master.MasterPositionController import MasterPositionController
import threading

api_routes = Blueprint('api_routes', __name__)

bot_thread = None
bot_running = False

@api_routes.route('/run', methods=['POST'])
def run():
    '''Main.run:run'''
    global bot_thread, bot_running
    if not bot_running:
        bot_running = True
        bot_thread = threading.Thread(target=main_run.run)
        bot_thread.start()
        return jsonify({"status": "Running..."}), 200
    else:
        return jsonify({"status": "Bot already running..."}), 200


@api_routes.route('/stop', methods=['POST'])
def stop():
    global bot_running
    if bot_running:
        pub.sendMessage("stop_bot")
        bot_running = False
        return jsonify({"status": "Bot stopping..."})
    else:
        return jsonify({"status": "Bot is not running"})

'''Main.run:demo'''
@api_routes.route('/demo', methods=['POST'])
def demo():
    '''Main.run:demo'''
    main_run.demo()
    print("Running demo...")
    return jsonify({"status": "Running demo..."})


# TxExecution.Master.run:main
@api_routes.route('/close-position/<id>', methods=['POST'])
def close_position(id):
    # symbol=args.symbol, reason=PositionCloseReason.TEST.value, exchanges=exchanges
    MasterPositionController.run(id)
    return jsonify({"status": "Closing position..."})


@api_routes.route('/status', methods=['GET'])
def status():
    global bot_running
    return jsonify({"status": "running" if bot_running else "stopped"})

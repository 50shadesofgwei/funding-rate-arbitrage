from flask import Blueprint, jsonify
import Main.run as main_run
import TxExecution.Synthetix.run as synthetix_run
import TxExecution.Master.run as tx_master_run
from pubsub import pub
# from PositionMonitor.TradeDatabase.TradeDatabase import 

api_routes = Blueprint('api_routes', __name__)


@api_routes.route('/run', methods=['POST'])
def run():
    '''Main.run:run'''
    # TODO: Check bot-status from database
    main_run.run()
    return jsonify({"status": "Running..."})

@api_routes.route('/stop', methods=['POST'])
def stop():
    '''
        If bot is running transmit signal to stop the bot
    '''
    # TODO: Check bot-status from database
    pub.sendMessage("stop_bot")
    return jsonify({"status": "Signal transmitted"}), 200

'''Main.run:demo'''
@api_routes.route('/demo', methods=['POST'])
def demo():
    '''Main.run:demo'''
    main_run.demo()
    print("Running demo...")
    return jsonify({"status": "Running demo..."})

# TxExecution.Synthetix.run:main
@api_routes.route('/deploy-collateral-synthetix', methods=['POST'])
def deploy_collateral_synthetix():
    synthetix_run.main()
    return jsonify({"status": "Deploying collateral to Synthetix..."})

# TxExecution.Master.run:main
@api_routes.route('/close-position/<id>', methods=['POST'])
def close_position(id):
    # Verify if the position is open

    tx_master_run.run(id)
    return jsonify({"status": "Closing position..."})

@api_routes.route('/status')
def status():
    main_run

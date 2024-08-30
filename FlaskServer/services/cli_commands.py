from flask import Blueprint, jsonify
import Main.run as main_run
import TxExecution.Synthetix.run as synthetix_run
import TxExecution.Master.run as tx_master_run
# from PositionMonitor.TradeDatabase.TradeDatabase import 

api_routes = Blueprint('api_routes', __name__)

# Define your routes here

api_routes = Blueprint('api_routes', __name__)


@api_routes.route('/run', methods=['POST'])
def run():
    '''Main.run:run'''
    main_run.run()
    print("Running main...")
    return jsonify({"status": "Running..."})

@api_routes.route('/stop-bot', methods=['POST'])
def pause_run():
    '''
        Allow bot to finish current trade-execution and stop the bot
    '''
    main_run.stop_bot()
    return jsonify({"status": "Bot stopped..."})

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


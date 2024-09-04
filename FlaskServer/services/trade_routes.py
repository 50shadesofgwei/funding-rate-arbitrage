from flask import Blueprint, jsonify, current_app
from TxExecution.Master.MasterPositionController import MasterPositionController
from APICaller.master.MasterUtils import get_target_exchanges

routes = Blueprint('db_routes', __name__, url_prefix='/trades')

@routes.route('/all', methods=['GET'])
def get_trades():
    trade_logger = current_app.trade_logger     # Note that current current_app only works in the context of a request (creates a Request and App context)
    return jsonify(trade_logger.get_all_trades())


# TODO: Add route for getting all strategy_exchange_id

# TODO: Add route for getting specific strategy_exchange_id

@routes.route('/collateral/<exchange>')
def get_deployed_collateral(exchange: str):
    """
        Get Collateral in each Perps Market
    """
    target_exchanges = get_target_exchanges()
    if exchange in target_exchanges:
        master_position_caller = MasterPositionController()
        collateral: float = master_position_caller.get_available_collateral_for_exchange(exchange=exchange)
        return jsonify(collateral), 200
    else:
        return jsonify("Invalid Exchange!"), 400
    
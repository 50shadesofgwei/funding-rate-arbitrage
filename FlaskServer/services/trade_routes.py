from flask import Blueprint, jsonify, current_app

from GlobalUtils.globalUtils import EventsDirectory

routes = Blueprint('db_routes', __name__, url_prefix='/trades')

@routes.route('/all', methods=['GET'])
def get_trades():
    trade_logger = current_app.trade_logger     # Note that current current_app only works in the context of a request (creates a Request and App context)
    return jsonify(trade_logger.get_all_trades())

@routes.route('/schema', methods=['GET'])
def get_trade_schema():
    trade_logger = current_app.trade_logger
    return jsonify(trade_logger.get_schema())

# TODO: Add route for getting all strategy_exchange_id

# TODO: Add route for getting specific strategy_exchange_id
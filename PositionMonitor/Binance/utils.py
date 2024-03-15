

def get_dict_from_database_response(response):
    columns = [
        'id', 'strategy_execution_id', 'order_id', 'exchange', 'symbol',
        'side', 'size', 'open_close', 'open_time', 'close_time',
        'pnl', 'position_delta', 'close_reason'
    ]
    response_dict = {columns[i]: response[i] for i in range(len(columns))}

    return response_dict


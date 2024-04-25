import pandas as pd

def determine_trade_entry_exit_points(data_snx: pd.DataFrame, data_binance: pd.DataFrame, threshold):
    trades = []
    binance_blocks = data_binance.set_index('block_number')

    for index, row in data_snx.iterrows():
        block_number_snx = row['block_number']
        nearest_binance_index = binance_blocks.index.get_loc(block_number_snx, method='nearest')
        nearest_binance_block = binance_blocks.iloc[nearest_binance_index]

        snx_rate = row['funding_rate']
        binance_rate = nearest_binance_block['funding_rate']
        discrepancy = snx_rate - binance_rate

        if abs(discrepancy) > threshold:
            trade = {
                'block_number_snx': block_number_snx,
                'block_number_binance': nearest_binance_block.name,
                'snx_rate': snx_rate,
                'binance_rate': binance_rate,
                'discrepancy': discrepancy,
                'snx_side': 'short' if snx_rate > binance_rate else 'long',
                'binance_side': 'long' if snx_rate > binance_rate else 'short'
            }
            trades.append(trade)

    return trades


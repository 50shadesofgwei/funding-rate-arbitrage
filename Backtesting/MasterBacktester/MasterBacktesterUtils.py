import pandas as pd
from GlobalUtils.logger import logger
import numpy as np
import matplotlib.pyplot as plt

def determine_trade_entry_exit_points(data_snx: pd.DataFrame, data_binance: pd.DataFrame, entry_threshold: float, exit_threshold: float):
    trades = []
    data_snx['funding_rate'] = data_snx['funding_rate'].astype(float)
    data_binance['funding_rate'] = data_binance['funding_rate'].astype(float)

    data_binance['block_number'] = data_binance['block_number'].astype(int)
    data_snx['block_number'] = data_snx['block_number'].astype(int)

    binance_blocks = data_binance['block_number'].values

    open_trade = None

    for index, row in data_snx.iterrows():
        block_number_snx = row['block_number']
        nearest_index = np.abs(binance_blocks - block_number_snx).argmin()
        nearest_binance_row = data_binance.iloc[nearest_index]

        snx_rate = row['funding_rate']
        binance_rate = nearest_binance_row['funding_rate']
        discrepancy = snx_rate - binance_rate

        if abs(discrepancy) > entry_threshold and not open_trade:
            base_position_size = 10
            snx_position_size = -base_position_size if snx_rate > binance_rate else base_position_size
            binance_position_size = base_position_size if snx_rate > binance_rate else -base_position_size
            open_trade = {
                'entry_block_snx': block_number_snx,
                'entry_block_binance': nearest_binance_row['block_number'],
                'snx_rate_entry': snx_rate,
                'binance_rate_entry': binance_rate,
                'discrepancy_entry': discrepancy,
                'snx_side': 'short' if snx_rate > binance_rate else 'long',
                'binance_side': 'long' if snx_rate > binance_rate else 'short',
                'snx_position_size': snx_position_size,
                'binance_position_size': binance_position_size
            }

        elif open_trade and abs(discrepancy) < exit_threshold:
            open_trade.update({
                'exit_block_snx': block_number_snx,
                'exit_block_binance': nearest_binance_row['block_number'],
                'snx_rate_exit': snx_rate,
                'binance_rate_exit': binance_rate,
                'discrepancy_exit': discrepancy
            })
            trades.append(open_trade)
            open_trade = None

    if open_trade:
        last_row = data_snx.iloc[-1]
        last_binance_row = data_binance.iloc[np.abs(data_binance['block_number'].values - last_row['block_number']).argmin()]
        open_trade.update({
            'exit_block_snx': last_row['block_number'],
            'exit_block_binance': last_binance_row['block_number'],
            'snx_rate_exit': last_row['funding_rate'],
            'binance_rate_exit': last_binance_row['funding_rate'],
            'discrepancy_exit': last_row['funding_rate'] - last_binance_row['funding_rate']
        })
        trades.append(open_trade)

    return trades

def calculate_profit_or_loss_for_trade(trade, snx_funding_impact, binance_funding_impact):
    snx_profit = snx_funding_impact * (trade['snx_side'] == 'short' and -1 or 1)
    binance_profit = binance_funding_impact * (trade['binance_side'] == 'long' and 1 or -1)
    total_profit = snx_profit + binance_profit
    time_open = trade['exit_block_snx'] - trade['entry_block_binance']
    
    trade_details = {
        'entry': {
            'snx': trade['entry_block_snx'],
            'binance': trade['entry_block_binance']
        },
        'exit': {
            'snx': trade['exit_block_snx'],
            'binance': trade['exit_block_binance']
        },
        'discrepancy': {
            'entry': trade['discrepancy_entry'],
            'exit': trade['discrepancy_exit']
        },
        'time_open_in_blocks': time_open,
        'position_size': {
            'snx': trade['snx_position_size'],
            'binance': trade['binance_position_size']
        },
        'profit': {
            'snx': snx_profit,
            'binance': binance_profit,
            'total': total_profit
        },
        'side': {
            'snx': trade['snx_side'],
            'binance': trade['binance_side']
        }
    }
    
    return trade_details

def calculate_effective_APR(trades, total_profit, base_trade_size):
    if not trades:
        return 0 

    start_block = trades[0]['entry']['snx']
    end_block = trades[-1]['exit']['snx'] 
    total_blocks = end_block - start_block
    total_seconds = total_blocks * 2 
    years = total_seconds / 31_536_000 
    total_capital = base_trade_size

    if years == 0:
        return float('inf')

    apr = (total_profit / total_capital) / years * 100
    return apr

def log_trade_details(trade):
    logger.info(f"Trade Log: {trade}")

def plot_funding_rates_over_time(synthetix_data, binance_data, symbol: str):
    plt.figure(figsize=(12, 6))
    plt.plot(synthetix_data['block_number'], synthetix_data['funding_rate'], label='Synthetix Funding Rate', color='blue')
    plt.plot(binance_data['block_number'], binance_data['funding_rate'], label='Binance Funding Rate', color='red')
    plt.title(f'Funding Rates on Binance vs Synthetix Over Time - Asset: {symbol}')
    plt.xlabel('Block Number')
    plt.ylabel('Funding Rate')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_funding_rate_discrepancies_over_time(synthetix_data: pd.DataFrame, binance_data: pd.DataFrame, symbol: str):
    # Ensure the data is sorted by block number
    synthetix_data = synthetix_data.sort_values('block_number').reset_index(drop=True)
    binance_data = binance_data.sort_values('block_number').reset_index(drop=True)

    # Merge data on nearest block number
    synthetix_data['nearest_block'] = synthetix_data['block_number']
    binance_data['nearest_block'] = binance_data['block_number']

    # Using merge_asof to find the nearest block numbers for discrepancies
    combined_data = pd.merge_asof(synthetix_data, binance_data, on='nearest_block', suffixes=('_snx', '_binance'), direction='nearest')
    combined_data['discrepancy'] = combined_data['funding_rate_snx'] - combined_data['funding_rate_binance']

    plt.figure(figsize=(12, 6))
    plt.plot(combined_data['nearest_block'], combined_data['discrepancy'], label='Funding Rate Discrepancy', color='blue')
    plt.title(f'Funding Rate Discrepancy - Asset: {symbol}')
    plt.xlabel('Block Number')
    plt.ylabel('Discrepancy')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_discrepancies_with_trades(synthetix_data: pd.DataFrame, binance_data: pd.DataFrame, trades, symbol: str):
    synthetix_data = synthetix_data.sort_values('block_number').reset_index(drop=True)
    binance_data = binance_data.sort_values('block_number').reset_index(drop=True)

    combined_data = pd.merge_asof(synthetix_data, binance_data, on='block_number', suffixes=('_snx', '_binance'), direction='nearest')
    combined_data['discrepancy'] = combined_data['funding_rate_snx'] - combined_data['funding_rate_binance']

    plt.figure(figsize=(12, 6))
    plt.plot(combined_data['block_number'], combined_data['discrepancy'], label='Funding Rate Discrepancy', color='red')

    entry_blocks = [trade['entry']['snx'] for trade in trades]
    exit_blocks = [trade['exit']['snx'] for trade in trades]
    entry_discrepancies = [combined_data.loc[combined_data['block_number'] == block, 'discrepancy'].values[0] if not combined_data[combined_data['block_number'] == block].empty else None for block in entry_blocks]
    exit_discrepancies = [combined_data.loc[combined_data['block_number'] == block, 'discrepancy'].values[0] if not combined_data[combined_data['block_number'] == block].empty else None for block in exit_blocks]

    plt.scatter(entry_blocks, entry_discrepancies, color='green', label='Entry Points', marker='^', s=100)
    plt.scatter(exit_blocks, exit_discrepancies, color='black', label='Exit Points', marker='v', s=100)

    plt.title(f'Funding Rate Discrepancy w/ Trades - Asset: {symbol}')
    plt.xlabel('Block Number')
    plt.ylabel('Discrepancy')
    plt.legend()
    plt.grid(True)
    plt.show()

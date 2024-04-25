from Backtesting.Binance.binanceBacktester import BinanceBacktester
from Backtesting.Synthetix.SynthetixBacktester import SynthetixBacktester
from Backtesting.utils.backtestingUtils import *
from APICaller.master.MasterUtils import TARGET_TOKENS
from GlobalUtils.logger import logger
import time
import pandas as pd
import matplotlib.pyplot as plt

class MasterBacktester:
    def __init__(self):
        self.binance = BinanceBacktester()
        self.synthetix = SynthetixBacktester()

    def run_updates(self):
        """Iterate over each token in TARGET_TOKENS and update data."""
        try:
            for token_info in TARGET_TOKENS:
                if token_info["is_target"]:
                    self.binance.get_historical_data(token_info["token"])
                    time.sleep(3)
                    self.synthetix.get_and_save_historical_data(token_info["token"])
                    time.sleep(3)
        except Exception as e:
            logger.error(f'MasterBacktester - Error encountered while updating data: {e}')

    def find_nearest_binance_entry(self, synthetix_block_number, binance_df):
        time_diffs = abs(binance_df['block_number'] - synthetix_block_number)
        idx_nearest = time_diffs.idxmin()

        return binance_df.loc[idx_nearest, 'funding_rate']

    def analyse_data(self, symbol: str):
        synthetix_data = self.synthetix.load_data_from_json(symbol)
        binance_data = self.binance.load_data_from_json(symbol)

        synthetix_df = pd.DataFrame(synthetix_data)
        binance_df = pd.DataFrame(binance_data)

        binance_df['funding_rate'] = pd.to_numeric(binance_df['funding_rate'])
        synthetix_df['nearest_binance_funding_rate'] = synthetix_df['block_number'].apply(
            lambda bn: self.find_nearest_binance_entry(bn, binance_df)
        )
        synthetix_df['funding_rate_discrepancy'] = synthetix_df['funding_rate'] - synthetix_df['nearest_binance_funding_rate']
        arbitrage_opportunities = synthetix_df[synthetix_df['funding_rate_discrepancy'].abs() > 0.0001]

        return_value = {
            "snx": synthetix_df,
            "binance": binance_df
        }

        return return_value

    
    def backtest_arbitrage_strategy(self, synthetix_funding_events, binance_funding_events: list, entry_threshold=0.0001, exit_threshold=0.00005):
        synthetix_df = pd.DataFrame(synthetix_funding_events)
        binance_df = pd.DataFrame(binance_funding_events).sort_values('block_number')

        open_position = False
        position_size_eth = 0.0
        total_profit = 0.0
        entry_details = {}

        trades = []

        binance_idx = 0

        for i, row in synthetix_df.iterrows():
            funding_rate_snx = row['funding_rate']
            block_number_snx = row['block_number']

            while binance_idx < len(binance_df) and block_number_snx >= binance_df.iloc[binance_idx]['block_number']:
                last_binance_block = binance_df.iloc[binance_idx]['block_number']
                binance_funding_rate = float(binance_df.iloc[binance_idx]['funding_rate'])
                if open_position:
                    binance_funding_paid = binance_funding_rate * -position_size_eth  # Opposite position for Binance
                binance_idx += 1

            funding_discrepancy = funding_rate_snx - binance_funding_rate

            if abs(funding_discrepancy) > entry_threshold and not open_position:
                position_size_eth = float(row['skew'] / 2)
                open_position = True
                entry_details = {
                    'entry_block': block_number_snx,
                    'entry_funding_rate_snx': funding_rate_snx,
                    'entry_funding_rate_binance': binance_funding_rate if open_position else 0,
                    'entry_discrepancy': funding_discrepancy
                }

            if open_position and (abs(funding_discrepancy) < exit_threshold or i == len(synthetix_df) - 1):
                snx_pnl = funding_rate_snx * position_size_eth
                binance_pnl = -binance_funding_paid  # PnL for opposite position
                total_pnl = snx_pnl + binance_pnl  # Correcting total PnL calculation
                total_profit += total_pnl
                trades.append({
                    'synthetix': {
                        'entry_block': entry_details['entry_block'],
                        'exit_block': block_number_snx,
                        'position_size_eth': position_size_eth,
                        'pnl': snx_pnl
                    },
                    'binance': {
                        'entry_block': entry_details['entry_block'],
                        'exit_block': block_number_snx,
                        'position_size_eth': -position_size_eth,  # Opposite position size
                        'pnl': binance_pnl
                    },
                    'joint': {
                        'total_pnl': total_pnl,
                        'entry_discrepancy': entry_details['entry_discrepancy'],
                        'exit_discrepancy': funding_discrepancy
                    }
                })
                open_position = False

        # Print detailed trade logs
        for trade in trades:
            print(f"Synthetix Trade Details: {trade['synthetix']}")
            print(f"Binance Trade Details: {trade['binance']}")
            print(f"Joint Trade Details: {trade['joint']}")

        return total_profit


entry_threshold = 0.0001
exit_threshold = 0.00005 

x = MasterBacktester()
y = x.binance.load_data_from_json('ETH')
z = x.synthetix.load_data_from_json('ETH')

profit = x.backtest_arbitrage_strategy(z, y)
print(f"Total Profit from Arbitrage Strategy: {profit}")

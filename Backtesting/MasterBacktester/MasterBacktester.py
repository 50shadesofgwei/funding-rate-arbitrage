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

    def backtest_arbitrage_strategy(self, synthetix_df, binance_funding_events, entry_threshold=0.0001, exit_threshold=0.00005):
        open_position = False
        position_size_eth = 0
        total_profit = 0.0
        synthetix_funding_paid = 0.0
        binance_funding_paid = 0.0
        last_binance_block = 0  # Track the last binance block that had a funding event

        binance_funding_events = {int(entry['block_number']): float(entry['funding_rate']) for entry in binance_funding_events}
        sorted_binance_events = sorted(binance_funding_events.items(), key=lambda x: x[0])

        for i, row in synthetix_df.iterrows():
            funding_rate_snx = row['funding_rate']
            funding_velocity_snx = row['funding_velocity']
            block_number_snx = row['block_number']

            # Check for the last Binance funding event before the current Synthetix block number
            while sorted_binance_events and block_number_snx >= sorted_binance_events[0][0]:
                last_binance_block, binance_funding_rate = sorted_binance_events.pop(0)
                if open_position:  # Apply Binance funding fee if we have an open position
                    binance_funding_paid += binance_funding_rate * position_size_eth


            funding_discrepancy = funding_rate_snx - binance_funding_paid

            if abs(funding_discrepancy) > entry_threshold and not open_position:
                position_size_eth = row['skew'] / 2
                open_position = True

            if abs(funding_discrepancy) < exit_threshold and open_position:
                profit = synthetix_funding_paid * position_size_eth
                total_profit += profit
                synthetix_funding_paid = 0.0
                binance_funding_paid = 0.0
                position_size_eth = 0
                open_position = False

        # Calculate any remaining profit if position is still open
        if open_position:
            profit = synthetix_funding_paid * position_size_eth
            total_profit += profit

        return total_profit

entry_threshold = 0.0001
exit_threshold = 0.00005 

x = MasterBacktester()
y = x.analyse_data('ETH')
profit = x.backtest_arbitrage_strategy(y['snx'], y['binance'])
print(f"Total Profit from Arbitrage Strategy: {profit}")

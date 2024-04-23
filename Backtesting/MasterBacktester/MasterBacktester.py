from Backtesting.Binance.binanceBacktester import BinanceBacktester
from Backtesting.Synthetix.SynthetixBacktester import SynthetixBacktester
from Backtesting.utils.backtestingUtils import *
import json
import pandas as pd
import matplotlib.pyplot as plt

class MasterBacktester:
    def __init__(self):
        self.binance = BinanceBacktester()
        self.synthetix = SynthetixBacktester()

    def build_data_object(self, symbol: str) -> dict:
        synthetix_data = self.synthetix.retrieve_and_process_events(symbol)
        binance_data = self.binance.build_backtest_data(symbol)

        synthetix_df = pd.DataFrame(synthetix_data)
        binance_df = pd.DataFrame(binance_data)

        binance_df.rename(columns={'markPrice': 'price'}, inplace=True)
        binance_df['price'] = pd.to_numeric(binance_df['price'])
        binance_df['funding_rate'] = pd.to_numeric(binance_df['funding_rate'])

        # Merging DataFrames on 'block_number' and 'market_id'
        combined_df = pd.merge(synthetix_df, binance_df, on=['market_id', 'block_number'], how='outer', suffixes=('_snx', '_binance'))

        combined_df['funding_rate_discrepancy'] = combined_df['funding_rate_snx'] - combined_df['funding_rate_binance']

        # Filter opportunities where discrepancies are significant
        arbitrage_opportunities = combined_df[combined_df['funding_rate_discrepancy'].abs() > 0.0001]

        plt.figure(figsize=(10, 5))
        plt.plot(combined_df['block_number'], combined_df['funding_rate_discrepancy'], marker='o', linestyle='-', color='blue')
        plt.title('Funding Rate Discrepancies Between Synthetix and Binance')
        plt.xlabel('Block Number')
        plt.ylabel('Funding Rate Discrepancy')
        plt.grid(True)
        plt.show()
        return combined_df

x = MasterBacktester()
y = x.build_data_object("ETH")

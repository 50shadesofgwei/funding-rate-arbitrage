from Backtesting.Binance.binanceBacktester import BinanceBacktester
from Backtesting.Synthetix.SynthetixBacktester import SynthetixBacktester
from Backtesting.utils.backtestingUtils import *
from Backtesting.Binance.binanceBacktesterUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import *
from Backtesting.MasterBacktester.MasterBacktesterUtils import *
from APICaller.master.MasterUtils import TARGET_TOKENS
from GlobalUtils.logger import logger
from GlobalUtils.marketDirectory import MarketDirectory
import time
import pandas as pd
import matplotlib.pyplot as plt

class MasterBacktester:
    def __init__(self):
        self.binance = BinanceBacktester()
        self.synthetix = SynthetixBacktester()

    def run_updates(self):
        try:
            self.synthetix.fetch_and_process_events_for_all_tokens()

            for token_info in TARGET_TOKENS:
                if token_info["is_target"]:
                    self.binance.get_historical_data(token_info["token"])
                    time.sleep(3)
        except Exception as e:
            logger.error(f'MasterBacktester - Error encountered while updating data: {e}')
    
    def backtest_arbitrage_strategy(self, symbol: str, entry_threshold=0.0001, exit_threshold=0.00005):
        try:
            synthetix_funding_events = self.synthetix.load_data_from_json(symbol)
            binance_funding_events = self.binance.load_data_from_json(symbol)

            synthetix_df = pd.DataFrame(synthetix_funding_events)
            binance_df = pd.DataFrame(binance_funding_events).sort_values('block_number')

            start_block: int = 16352864
            snx_df_filtered = synthetix_df.loc[synthetix_df['block_number'] > start_block]
            binance_df_filtered = binance_df.loc[binance_df['block_number'] > start_block]

            total_profit = 0.0
            trades = []

            potential_trades = determine_trade_entry_exit_points(snx_df_filtered, binance_df_filtered, entry_threshold, exit_threshold)

            for trade in potential_trades:
                trade_size_in_asset = trade['size_in_asset']
                binance_trade_events = extract_funding_events(binance_df, trade['entry_block_binance'], trade['exit_block_binance'])
                binance_funding_impact = calculate_total_funding_impact(binance_trade_events, trade_size_in_asset)

                new_funding_velocity = MarketDirectory.calculate_new_funding_velocity(symbol, trade_size_in_asset, trade_size_in_asset)
                synthetix_trade_data = synthetix_df[(synthetix_df['block_number'] >= trade['entry_block_snx']) & (synthetix_df['block_number'] <= trade['exit_block_snx'])]
                synthetix_funding_impact = accumulate_funding_costs(synthetix_trade_data, trade['entry_block_snx'], trade['exit_block_snx'], trade_size_in_asset)

                trade_details = calculate_profit_or_loss_for_trade(trade, synthetix_funding_impact, binance_funding_impact)
                trades.append(trade_details)
                total_profit += trade_details['profit']['total']

            return total_profit
        
        except Exception as e:
            logger.error(f'MasterBacktester - Error while backtesting arbitrage strategy for symbol {symbol}: {e}')
            return None

x = MasterBacktester()
MarketDirectory.initialize()
y = x.backtest_arbitrage_strategy('BTC')
print(y)



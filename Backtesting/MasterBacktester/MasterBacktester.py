from Backtesting.Binance.binanceBacktester import BinanceBacktester
from Backtesting.Synthetix.SynthetixBacktester import SynthetixBacktester
from Backtesting.utils.backtestingUtils import *
from Backtesting.Binance.binanceBacktesterUtils import *
from Backtesting.Synthetix.SynthetixBacktesterUtils import *
from Backtesting.MasterBacktester.MasterBacktesterUtils import *
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
            self.synthetix.fetch_and_process_events_for_all_symbols()

            for token_info in TARGET_TOKENS:
                if token_info["is_target"]:
                    self.binance.get_historical_data(token_info["token"])
                    time.sleep(3)
        except Exception as e:
            logger.error(f'MasterBacktester - Error encountered while updating data: {e}')
    
    def backtest_arbitrage_strategy(self, symbol: str, entry_threshold=0.0001, exit_threshold=0.00005):
        synthetix_funding_events = self.synthetix.load_data_from_json(symbol)
        binance_funding_events = self.binance.load_data_from_json(symbol)

        synthetix_df = pd.DataFrame(synthetix_funding_events)
        binance_df = pd.DataFrame(binance_funding_events).sort_values('block_number')

        total_profit = 0.0
        trades = []

        potential_trades = determine_trade_entry_exit_points(synthetix_df, binance_df, entry_threshold, exit_threshold)

        for trade in potential_trades:
            binance_trade_events = extract_funding_events(binance_df, trade['entry_block_binance'], trade['exit_block_binance'])
            binance_funding_impact = calculate_total_funding_impact(binance_trade_events, trade['binance_position_size'])

            synthetix_trade_data = synthetix_df[(synthetix_df['block_number'] >= trade['entry_block_snx']) & (synthetix_df['block_number'] <= trade['exit_block_snx'])]
            synthetix_funding_impact = accumulate_funding_costs(synthetix_trade_data, trade['entry_block_snx'], trade['exit_block_snx'], trade['snx_position_size'])

            trade_details = calculate_profit_or_loss_for_trade(trade, synthetix_funding_impact, binance_funding_impact)
            trades.append(trade_details)
            total_profit += trade_details['profit']['total']

        x = calculate_effective_APR(trades, total_profit, base_trade_size=2)
        logger.info(f'APR calculated at: {x}')

        plot_funding_rates_over_time(synthetix_df, binance_df, symbol)
        plot_discrepancies_with_trades(synthetix_df, binance_df, trades, symbol)

        return total_profit





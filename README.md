# Synthetix Funding Rate Arbitrage
![Funding Rate Arbitrage Bot Template](https://github.com/50shadesofgwei/SynthetixFundingRateArbitrage/assets/111451828/eb931108-bdbb-4741-b2bc-def2de8e3370)
> **Version 0.1.0, Alpha**

![Static Badge](https://img.shields.io/badge/Telegram-blue?link=https%3A%2F%2Ft.me%2F%2BualID7ueKuJjMWJk) ![Static Badge](https://img.shields.io/badge/License-MIT-green)

This project serves as a template to help newer developers/traders start taking advantage of delta-neutral arbitrage opportunities between CEX/DEX perps platforms. Current version focuses on Synthetix vs Binance pairs, opening funding-accruing positions on Synthetix and hedging on Binance. 

Given that the repo is under active development, it is recommended that you run the bot on testnet for a while first to ensure that the configuration is correct before putting any capital at stake.

> *All code contained within this repository is distrubuted freely under the MIT License*

## Contributions
This repo is designed to be open source and as such we welcome any who is interested in contributing to the codebase. To reach out, join the Telegram chat linked at the bottom of the README.

## Getting Started

To start, first clone the repo using `git clone git@github.com:50shadesofgwei/SynthetixFundingRateArbitrage.git`.
After this, navigate to the .env file and input the necessary values. You will need:

- An Alchemy API key
- The relevant chainId (Base Mainnet: 8453, Base Testnet: 84532)
- Your wallet address and Private Key (For security reasons you should create a new wallet to use here)
- A Binance API key + secret
- A Coingecko API key

Recommended values for the following vars are as follows:
- `TRADE_LEVERAGE=5`
- `DELTA_BOUND=0.03`
- `PERCENTAGE_CAPITAL_PER_TRADE=25`

Trade Leverage specifies the leverage applied to the collateral amount on each trade. Setting this value too high will result in positions being liquidated, so keeping a relatively small cap is a good idea.
Delta Bound calculates the maximum delta on a trade pair before it will be cancelled by the health checker. The delta between positions will in most cases be 0.0, so this is mostly a failsafe.
Percentage Capital Per Trade specifies the amount of available capital to be used on each trade that is executed. This is derived by checking how much available collateral there is on each exchange, then taking the smaller value and calculating `(smallerValue/100)*PERCANTAGE_CAPITAL_PER_TRADE`. Higher values for this will of course make the trade sizes larger, and therefore will mean having to rebalance the collateral between exchanges more frequently.

## Dependenceies

Install dependenceies via navigating to the project directory 
`cd SynthetixFundingRateArbitrage` 
and running:
`pip install -r requirements.txt`

## Testnet config
To start executing some test trades, first you will need to mint some fUSDC on Base sepolia (you can do that [here](https://sepolia.basescan.org/address/0xa1ae612e07511a947783c629295678c07748bc7a#writeContract) by calling `deposit_eth` with some testnet Eth and '0x69980C3296416820623b3e3b30703A74e2320bC8' as the token_address argument). 
After you have some fUSDC, you can call the collateral deposit function by navigating to the SynthetixPositionController script and copy pasting this code to the bottom of the file:
```python
x = SynthetixPositionController()
token_address = '0x69980C3296416820623b3e3b30703A74e2320bC8' #fUSDC contract address
amount = 100000000 # example, 100 fUSDC
x.approve_and_deposit_collateral(token_address, amount)
```
And then running the script by entering `python3 TxExecution/Synthetix/SynthetixPositionController.py` into the CLI and clicking enter (this assumes you are in the root project directory already)

For the Binance side, you will have to create an account and set of API keys [here](https://testnet.binancefuture.com/en/futures/BTCUSDT), and use these keys in the .env file. Additionally, whether the Binance client is set to testnet or live trading is determined by 

## Architecture

The project is designed according to a modular, event-driven architecture where functionality is grouped together into like kind sub-classes, instances of which are then contained in a master class which itself is contained within the main class. To illustrate, let's look at the APICaller module contains all logic for calling funding rate data from the relevant APIs. This module contains two sub-classes `SynthetixCaller` and `BinanceCaller`, where all the logic for interacting with the respective APIs is stored in the corresponding sub-class. Then an instance of each class is stored within the `MasterCaller` class, which contains all functions that require access to both of these APIs, an example being reading and identifying funding rate discrepancies between the two.
This inheritance structure is repeated with the Master modules, an instance of each being created in the Main class. The Main class therefore contains instances of the following:
    - `MasterCaller`
    - `MatchingEngine`
    - `MasterPositionMonitor`
    - `MasterPositionController`
    - `TradeLogger`

Cross-module communication is handled via event emitters and listeners, a directory of which can be found in GlobalUtils.py.
Upon confirmation of execution, trades are logged to a database with each side (SNX/Binance) having its own entry, and are linked via a shared UUID. Upon closing, the entries are updated with relevant PnL, accrued funding and reason for close. 

## Open Issues / Potential Improvements
> **Version 0.1.0**

**Shutdown** 

If you're running an instance of the bot and shut it down mid-trade, the positions won't close automatically; you'll have to close them manually either via a UI or by using 
```python
x = Main()
x.MasterPositionController.close_all_positions()
``` 
on the main class.

**Slippage**

In its current form, the bot uses market orders for both sides of each trade. For Synthetix this is mandated by the smart contracts but for the Binance side, there is a possibility that one could tighten the profit margins on each trade by using limit orders instead of market orders. The slippage is especially pronounced on Binance testnet because there's such little liquidity and therefore the bid/ask spread is very large, which also makes backtesting and + test PnL calculations harder to run off of testnet data.

## Tech Support 
Any further questions please join the telegram chat at https://t.me/+ualID7ueKuJjMWJk
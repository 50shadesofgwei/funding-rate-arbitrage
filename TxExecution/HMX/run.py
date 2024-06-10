from TxExecution.HMX.HMXPositionController import HMXPositionController
import argparse

def run(args):
    x = HMXPositionController()
    x.deposit_erc20_collateral(token_address=args.token_address, amount=args.amount)

def main():
    parser = argparse.ArgumentParser(description="Approve and deposit collateral using the HMXPositionController")
    parser.add_argument('token_address', type=str, help='The address of the ERC20 token you want to deposit')
    parser.add_argument('amount', type=int, help='The amount of the token to deposit (in token decimals)')
    args = parser.parse_args()
    run(args)
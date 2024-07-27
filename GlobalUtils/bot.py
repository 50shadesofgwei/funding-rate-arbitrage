import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

def escape_markdown_decorator(func):
    def wrapper(self, *args, **kwargs):
        message = func(self, *args, **kwargs)
        return self.escape_markdown(message)
    return wrapper

class TelegramMessenger:
    def __init__(self):
        self.token = str(os.getenv('TELEGRAM_BOT_TOKEN'))
        self.chat_id = str(os.getenv('TELEGRAM_CHAT_ID'))

    def send_message(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "MarkdownV2"  # Using MarkdownV2 format
        }
        response = requests.post(url, json=payload)
        return response.json()

    def escape_markdown(self, text):
        """
        Escape special characters for Telegram MarkdownV2.
        """
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return ''.join(['\\' + char if char in escape_chars else char for char in text])

    @escape_markdown_decorator
    def format_opportunity(self, data):
        formatted_message = (
            f"*Long Exchange:* {data['long_exchange']}\n"
            f"*Short Exchange:* {data['short_exchange']}\n"
            f"*Symbol:* {data['symbol']}\n"
            f"*Long Exchange Funding Rate:* {data['long_exchange_funding_rate']:.6f}\n"
            f"*Short Exchange Funding Rate:* {data['short_exchange_funding_rate']:.6f}\n"
            f"*Long Exchange Skew:* {data['long_exchange_skew']:.2f}\n"
            f"*Short Exchange Skew:* {data['short_exchange_skew']:.2f}\n"
            f"*Block Number:* {data['block_number']}\n"
            f"*Trade Duration Estimate:* {data['trade_duration_estimate']:.2f} hours\n"
            f"*Total Profit (USD):* {data['total_profit_usd']:.2f}\n"
            f"*Long Exchange Profit (USD):* {data['long_exchange_profit_usd']:.2f}\n"
            f"*Short Exchange Profit (USD):* {data['short_exchange_profit_usd']:.2f}\n"
        )
        return formatted_message

    def report_opportunity(self, data):
        formatted_message = self.format_opportunity(data)
        response = self.send_message(formatted_message)
        return response

    @escape_markdown_decorator
    def format_account_info(self, account_info):
        message = "*Account Report*\n\n"
        for account, info in account_info.items():
            message += f"*{account}*\n"
            message += f"Position Value: {info['Position Value']}\n"
            message += f"Holding Nums: {info['Holding Nums']}\n"
            message += f"Margin Size: {info['Margin Size']}\n"
            message += f"Balance: {info['Balance']}\n\n"
        return message

    def report_account(self, data):
        formatted_message = self.format_account_info(data)
        response = self.send_message(formatted_message)
        return response

    @escape_markdown_decorator
    def format_order(self, order_details):
        message = "*Order Details Report*\n\n"
        message += f"*Exchange:* {order_details['exchange']}\n"
        message += f"*Symbol:* {order_details['symbol']}\n"
        message += f"*Side:* {order_details['side']}\n"
        message += f"*Size:* {order_details['size']}\n"
        message += f"*Order ID:* {order_details['order_id']}\n"
        message += f"*Liquidation Price:* {order_details['liquidation_price']:.2f}\n"
        return message

    def report_order(self, data):
        formatted_message = self.format_order(data)
        response = self.send_message(formatted_message)
        return response

    @escape_markdown_decorator
    def format_position_close(self, data):
        message = "*Position Close Report*\n\n"
        message += f"*Symbol:* {data['symbol']}\n"
        message += f"*Exchange:* {data['exchange']}\n"
        message += f"*PnL:* {data['pnl']:.2f}\n"
        message += f"*Accrued Funding:* {data['accrued_funding']:.2f}\n"
        message += f"*Reason:* {data['reason']}\n"
        return message

    def report_position_close(self, data):
        formatted_message = self.format_position_close(data)
        response = self.send_message(formatted_message)
        return response


    def report_holding(self, data):
        # 发送当前账户的每一笔持仓信息
        # 找到所有账户，然后遍历，print持仓

        pass


    def report_risk(self, data):
        pass
    # CLOSE_ALL_POSITIONS = "close_all_positions"
    # CLOSE_POSITION_PAIR = "close_position_pair"
    # OPPORTUNITY_FOUND = "opportunity_found"
    # POSITION_OPENED = "position_opened"
    # POSITION_CLOSED = "position_closed"
    # TRADE_LOGGED = "trade_logged"


def generate_test_data():

    account_info_data = {
        "account1": {
            "Position Value": random.uniform(1000, 10000),
            "Holding Nums": random.randint(1, 100),
            "Margin Size": random.uniform(100, 1000),
            "Balance": random.uniform(1000, 10000)
        },
        "account2": {
            "Position Value": random.uniform(1000, 10000),
            "Holding Nums": random.randint(1, 100),
            "Margin Size": random.uniform(100, 1000),
            "Balance": random.uniform(1000, 10000)
        }
    }

    order_data = {
        'exchange': random.choice(["Binance", "OKX", "Bitfinex"]),
        'symbol': random.choice(["BTCUSDT", "ETHUSDT", "DOGEUSDT"]),
        'side': random.choice(["Buy", "Sell"]),
        'size': random.randint(1, 100),
        'order_id': str(random.randint(100000, 999999)),
        'liquidation_price': random.uniform(1000, 10000)
    }

    position_close_data = {
        'symbol': random.choice(["BTCUSDT", "ETHUSDT", "DOGEUSDT"]),
        'exchange': random.choice(["Binance", "OKX", "Bitfinex"]),
        'pnl': random.uniform(-500, 1500),
        'accrued_funding': random.uniform(0, 100),
        'reason': random.choice(["Target reached", "Stop loss", "Manual close"])
    }

    return opportunity_data, account_info_data, order_data, position_close_data

if __name__ == "__main__":

    demo_opportunity_data = {
        "long_exchange": "Synthetix",
        "short_exchange": "HMX",
        "symbol": "DOGE",
        "long_exchange_funding_rate": 0.0005762749087086467,
        "short_exchange_funding_rate": 0.0005846459983723924,
        "long_exchange_skew": 1407.3356729161799,
        "short_exchange_skew": 19982.966103749997,
        "block_number": 17435285,
        "trade_duration_estimate": 8.0,
        "total_profit_usd": 4.98261742385525,
        "long_exchange_profit_usd": 4.9739435816360675,
        "short_exchange_profit_usd": 0.008673842219182425
    }

    sender = TelegramMessenger()

    account_info_data, order_data, position_close_data = generate_test_data()

    # Test report_opportunity
    sender.report_opportunity(demo_opportunity_data)

    # Test report_account
    sender.report_account(account_info_data)

    # Test report_order
    sender.report_order(order_data)

    # Test report_position_close
    sender.report_position_close(position_close_data)
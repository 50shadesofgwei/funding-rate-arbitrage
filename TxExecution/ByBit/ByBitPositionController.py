from pybit.unified_trading import HTTP
from APICaller.ByBit.ByBitUtils import *
from pubsub import pub
import os
from dotenv import load_dotenv
import requests

load_dotenv()

class ByBitPositionController:
    
    def __init__(self):
        self.client = get_ByBit_client()
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')

    def is_already_position_open(self) -> bool:
        url = "https://api.bybit.com/private/linear/position/list"
        headers = {
            "X-Api-Key": self.api_key,
            "X-Api-Secret": self.api_secret
        }
        response = requests.get(url, headers=headers)
        positions = response.json().get('result', [])
        
        for position in positions:
            if position.get('size', 0) > 0:
                return True
        return False

    def derive_position_to_open_from_opportunity(self, opportunity):
        test = ''

    
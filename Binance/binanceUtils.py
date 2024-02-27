import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

class BinanceEnvVars(Enum):
    API_KEY = "BINANCE_API_KEY"
    API_SECRET = "BINANCE_API_SECRET"
    
    def get_value(self):
        value = os.getenv(self.value)
        if value is None:
            raise ValueError(f"Environment variable for {self.name} not found.")
        return value
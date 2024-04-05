from APICaller.Binance.binanceCaller import BinanceCaller
import math

class BinanceBacktester:
    def __init__(self) -> None:
        self.caller = BinanceCaller()

    def get_weekly_average_rate(self, symbol: str) -> float:
        average_rate = self._calculate_average_funding_rate_for_period(symbol, period_days=7)
        return average_rate

    def get_monthly_average_rate(self, symbol: str) -> float:
        average_rate = self._calculate_average_funding_rate_for_period(symbol, period_days=30)
        return average_rate

    def get_yearly_average_rate(self, symbol: str) -> float:
        average_rate = self._calculate_average_funding_rate_for_period(symbol, period_days=math.floor(1000/3))
        return average_rate

    def _calculate_average_funding_rate_for_period(self, symbol: str, period_days: int) -> float:
        limit = period_days * 3
        historical_rates = self.caller.get_historical_funding_rate_for_symbol(symbol, limit)

        rate_total: float = 0
        for rate in historical_rates:
            funding_rate = float(rate['fundingRate'])
            rate_total = rate_total + funding_rate
        
        mean_rate_for_period = rate_total / limit
        return mean_rate_for_period


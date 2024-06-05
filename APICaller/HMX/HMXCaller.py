from GlobalUtils.globalUtils import *
from GlobalUtils.logger import logger

class HMXCaller:
    def __init__(self):
        self.client = GLOBAL_HMX_CLIENT

    def get_funding_rates(self, symbols: list) -> dict:
        if not symbols:
            logger.error("HMXCaller - No symbols provided to fetch funding rates.")
            return None

        try:
            all_market_data = self.client.public.get_all_market_info()
            logger.warning(f'all_market_data = {all_market_data}')
            if not all_market_data:
                logger.error("HMXCaller - Retrieved empty market data from API.")
                return None

            funding_rates = self._filter_market_data(all_market_data=all_market_data, symbols=symbols)
            if not funding_rates:
                logger.error(f"HMXCaller - No funding rates found for provided symbols: {symbols}")
                return None

            return funding_rates
        except KeyError as ke:
            logger.error(f"HMXCaller - KeyError while getting and filtering funding rates: Error: {ke}")
        except ValueError as ve:
            logger.error(f"HMXCaller - ValueError while getting and filtering funding rates: Error: {ve}")
        except Exception as e:
            logger.error(f"HMXCaller - Unexpected error while processing data for symbol: Error {e}")




    def _filter_market_data(self, all_market_data: dict, symbols: list) -> list:
        if not all_market_data:
            logger.error("HMXCaller - No market data provided for filtering.")
            return None

        if not symbols:
            logger.error("HMXCaller - No symbols provided for market data filtering.")
            return None

        try:
            market_funding_rates = []
            market: str = None
            market_data: dict = None
            for market_data in all_market_data.values():
                try:
                    market = market_data['market']
                    if market not in symbols:
                        continue
                    
                    funding_rate_8H = float(market_data['funding_rate']['8H'])
                    market_price = float(market_data['price'])
                    borrowing_rate_8H = float(market_data['borrowing_rate']['8H'])
                    skew = float(market_data['long_size']) - float(market_data['short_size'])
                    maintenance_margin_fraction_bps = float(market_data['margin']['maintenance_margin_fraction_bps'])
                    initial_margin_fraction_bps = float(market_data['margin']['initial_margin_fraction_bps'])

                    market_funding_rates.append({
                        'exchange': 'HMX',
                        'symbol': market,
                        'price': market_price,
                        'skew': skew,
                        'funding_rate': funding_rate_8H,
                        'borrowing_rate': borrowing_rate_8H,
                        'initial_margin_fraction_bps': initial_margin_fraction_bps,
                        'maintenance_margin_fraction_bps': maintenance_margin_fraction_bps
                    })

                except KeyError as ke:
                    logger.error(f"HMXCaller - KeyError accessing data for symbol {market}: {ke}")
                except ValueError as ve:
                    logger.error(f"HMXCaller - ValueError converting data for symbol {market}: {ve}")
                except Exception as e:
                    logger.error(f"HMXCaller - Unexpected error while processing data for symbol {market}: {e}")

            if not market_funding_rates:
                logger.warning(f"HMXCaller - No market data matched the provided symbols: {symbols}")

            return market_funding_rates
        
        except Exception as e:
            logger.error(f"HMXCaller - Failed to process market data: {e}")
            return []

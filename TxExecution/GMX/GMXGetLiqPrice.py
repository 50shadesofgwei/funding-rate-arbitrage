from gmx_python_sdk.gmx_python_sdk.scripts.v2.gmx_utils import *
import hashlib
from APICaller.GMX.GMXContractUtils import *
from gmx_python_sdk.gmx_python_sdk.scripts.v2.get.get_open_positions import GetOpenPositions
from gmx_python_sdk.gmx_python_sdk.scripts.v2.gmx_utils import (
    get_reader_contract, get_datastore_contract,
    get_tokens_address_dict)
from gmx_python_sdk.gmx_python_sdk.scripts.v2.get.get import GetData
from gmx_python_sdk.gmx_python_sdk.scripts.v2.get.get_oracle_prices import OraclePrices
from decimal import Decimal
from GlobalUtils.MarketDirectories.GMXMarketDirectory import GMXMarketDirectory


def calculate_liquidation_price(
    datastore_obj,
    market_address,
    index_token_address,
    size_in_usd: Decimal,
    size_in_tokens: Decimal,
    collateral_amount: Decimal,
    collateral_usd: Decimal,
    collateral_token: dict,
    pending_funding_fees_usd: Decimal,
    pending_borrowing_fees_usd: Decimal,
    min_collateral_usd: Decimal,
    is_long: bool,
    use_max_price_impact: bool = False,
    user_referral_info: dict = None
) -> Decimal:

    if size_in_usd <= 0 or size_in_tokens <= 0:
        return None

    index_token = index_token_address

    closing_fee_usd = get_position_fee(size_in_usd,
                                       True,
                                       user_referral_info)['positionFeeUsd']

    total_pending_fees_usd = get_position_pending_fees_usd(
        pending_funding_fees_usd, pending_borrowing_fees_usd)

    total_fees_usd = total_pending_fees_usd + closing_fee_usd

    maxPositionImpactFactorForLiquidations = datastore_obj.functions.getUint(
        max_position_impact_factor_for_liquidations_key(market_address)
    ).call()

    # max_negative_price_impact_usd = -1 * \
    #     apply_factor(size_in_usd, maxPositionImpactFactorForLiquidations)

    price_impact_delta_usd = 0

    # if use_max_price_impact:
    #     price_impact_delta_usd = max_negative_price_impact_usd
    # else:
    #     price_impact_delta_usd = get_price_impact_for_position(
    #         market_info, -size_in_usd, is_long, fallback_to_zero=True)

    #     if price_impact_delta_usd < max_negative_price_impact_usd:
    #         price_impact_delta_usd = max_negative_price_impact_usd

    #     # Ignore positive price impact
    #     if price_impact_delta_usd > 0:
    #         price_impact_delta_usd = Decimal(0)

    minCollateralFactor = datastore_obj.functions.getUint(
        minCollateralFactorKey(market_address)
    ).call()

    liquidation_collateral_usd = apply_factor(
        size_in_usd, minCollateralFactor)

    if liquidation_collateral_usd < min_collateral_usd:
        liquidation_collateral_usd = min_collateral_usd

    liquidation_price = Decimal(0)

    if get_is_equivalent_tokens(collateral_token, index_token):
        if is_long:
            denominator = size_in_tokens + collateral_amount
            if denominator == 0:
                return None

            liquidation_price = (
                (size_in_usd + liquidation_collateral_usd
                 - price_impact_delta_usd + total_fees_usd) / denominator
            )
            # TODO - add back in ) * 10**22
        else:
            denominator = size_in_tokens - collateral_amount

            if denominator == 0:
                return None

            liquidation_price = (
                (size_in_usd - liquidation_collateral_usd
                 + price_impact_delta_usd - total_fees_usd) / denominator
            )
            # TODO - add back in ) * 10**22
    else:
        if size_in_tokens == 0:
            return None

        remaining_collateral_usd = (collateral_usd + price_impact_delta_usd
                                    - total_pending_fees_usd - closing_fee_usd)

        if is_long:
            liquidation_price = (
                (liquidation_collateral_usd
                 - remaining_collateral_usd + size_in_usd) / size_in_tokens
            )
            # TODO - add back in ) * 10**22
        else:
            liquidation_price = (
                (liquidation_collateral_usd - remaining_collateral_usd
                 - size_in_usd) / - size_in_tokens
            )
            # TODO - add back in ) * 10**22

    if liquidation_price <= 0:
        return None

    return liquidation_price


def get_position_fee(
    size_delta_usd: Decimal,
    for_positive_impact: bool,
    referral_info: dict = None,
    ui_fee_factor: Decimal = Decimal(0)
) -> dict:

    factor = 0.0005 if for_positive_impact else 0.0007

    position_fee_usd = apply_factor(size_delta_usd,
                                    factor)

    return {
        'positionFeeUsd': position_fee_usd,
    }

def get_position_pending_fees_usd(pending_funding_fees_usd: Decimal, pending_borrowing_fees_usd: Decimal) -> Decimal:
    return pending_borrowing_fees_usd + pending_funding_fees_usd


def apply_factor(value, factor):
    return (value * factor) / 10**30


def get_price_impact_for_position(market_info, size_in_usd, is_long, fallback_to_zero):
    # Placeholder for the actual implementation
    return Decimal('0')


def get_is_equivalent_tokens(token1, token2):
    if token1 == token2:
        return True
    if token2 == "0x47904963fc8b2340414262125aF798B9655E58Cd":
        if token1 == "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f":
            return True
    return False


def get_position_key(account: str, market_address: str, collateral_address: str, is_long: bool) -> bytes:
    concatenated_string = f"{account}:{market_address}:{collateral_address}:{is_long}"
    hash_object = hashlib.sha256(concatenated_string.encode())
    return hash_object.digest()[:32]


def transform_to_dict(account_positions_list):
    result = []
    for pos in account_positions_list:
        position, referral, fees, base_pnl_usd, uncapped_base_pnl_usd, pnl_after_price_impact_usd = pos

        position_dict = {
            "position": {
                "addresses": {
                    "account": position[0][0],
                    "market": position[0][1],
                    "collateralToken": position[0][2],
                },
                "numbers": {
                    "sizeInUsd": position[1][0],
                    "sizeInTokens": position[1][1],
                    "collateralAmount": position[1][2],
                    "borrowingFactor": position[1][3],
                    "fundingFeeAmountPerSize": position[1][4],
                    "longTokenClaimableFundingAmountPerSize": position[1][5],
                    "shortTokenClaimableFundingAmountPerSize": position[1][6],
                    "increasedAtBlock": position[1][7],
                    "decreasedAtBlock": position[1][8],
                    "increasedAtTime": position[1][9],
                    "decreasedAtTime": position[1][10],
                },
                "flags": {
                    "isLong": position[2][0],
                },
            },
            "referral": {
                "referralCode": referral[0][0],
                "affiliate": referral[0][1],
                "trader": referral[0][2],
                "totalRebateFactor": referral[0][3],
                "traderDiscountFactor": referral[0][4],
                "totalRebateAmount": referral[0][5],
                "traderDiscountAmount": referral[0][6],
                "affiliateRewardAmount": referral[0][7],
            },
            "fees": {
                "fundingFeeAmount": referral[1][0],
                "claimableLongTokenAmount": referral[1][1],
                "claimableShortTokenAmount": referral[1][2],
                "latestFundingFeeAmountPerSize": referral[1][3],
                "latestLongTokenClaimableFundingAmountPerSize": referral[1][4],
                "latestShortTokenClaimableFundingAmountPerSize": referral[1][5],
            },
            "borrowing": {
                "borrowingFeeUsd": referral[2][0],
                "borrowingFeeAmount": referral[2][1],
                "borrowingFeeReceiverFactor": referral[2][2],
                "borrowingFeeAmountForFeeReceiver": referral[2][3],
            },
            "ui": {
                "uiFeeReceiver": referral[3][0],
                "uiFeeReceiverFactor": referral[3][1],
                "uiFeeAmount": referral[3][2],
            },
            "collateralTokenPrice": {
                "min": referral[4][0],
                "max": referral[4][1],
            },
            "positionFeeFactor": referral[5],
            "protocolFeeAmount": referral[6],
            "positionFeeReceiverFactor": referral[7],
            "feeReceiverAmount": referral[8],
            "feeAmountForPool": referral[9],
            "positionFeeAmountForPool": referral[10],
            "positionFeeAmount": referral[11],
            "totalCostAmountExcludingFunding": referral[12],
            "totalCostAmount": referral[13],
            "basePnlUsd": base_pnl_usd,
            "uncappedBasePnlUsd": uncapped_base_pnl_usd,
            "pnlAfterPriceImpactUsd": pnl_after_price_impact_usd,
        }

        result.append(position_dict)
    return result


def find_position(market_address, account_position):
    if market_address == account_position['position']['addresses']['market']:
        return True
    else:
        return False


def get_liquidation_price(config, symbol: str, is_long: bool):
    try:
        oracle_prices = OraclePrices(ARBITRUM_CONFIG_OBJECT.chain).get_recent_prices()
        positions = GetOpenPositions(ARBITRUM_CONFIG_OBJECT, ARBITRUM_CONFIG_OBJECT.user_wallet_address).get_data(oracle_prices)
        side = 'long' if is_long else 'short'
        position = positions[f'{symbol}_{side}']
        referral_storage = "0xe6fab3F0c7199b0d34d7FbE83394fc0e0D06e99d"
        datastore = "0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8"

        market_address = position["market"]

        data_obj = GetData(config=config, use_local_datastore=False,
                        filter_swap_markets=True)
        data_obj._get_token_addresses(market_address)
        market_info = data_obj.markets.get_available_markets()[market_address]

        index_token_address = market_info["index_token_address"]

        output = [data_obj._get_oracle_prices(market_address,
                                            index_token_address,
                                            oracle_prices,
                                            return_tuple=True)]

        hex_data = accountPositionListKey(ARBITRUM_CONFIG_OBJECT.user_wallet_address)
        reader_obj = get_reader_contract(config)
        datastore_obj = get_datastore_contract(config)
        position_keys = datastore_obj.functions.getBytes32ValuesAt(hex_data, 0, 1000).call()

        account_positions_list = []
        for i in position_keys:

            account_positions_list_raw = reader_obj.functions.getAccountPositionInfoList(
                datastore, referral_storage, [i], output, ARBITRUM_CONFIG_OBJECT.user_wallet_address).call()
            account_positions_list = transform_to_dict(account_positions_list_raw)

            account_positions_list += account_positions_list

        for account_position in account_positions_list:
            if find_position(market_address, account_position):
                break

        decimals = get_tokens_address_dict(config.chain)[
            account_position['position']['addresses']['collateralToken']]['decimals']

        liquidation_price = calculate_liquidation_price(
            datastore_obj=datastore_obj,
            market_address=market_address,
            index_token_address=index_token_address,
            size_in_usd=account_position['position']['numbers']['sizeInUsd'],
            size_in_tokens=account_position['position']['numbers']['sizeInTokens'],
            collateral_amount=account_position['position']['numbers']['collateralAmount'],
            collateral_usd=position['inital_collateral_amount_usd'][0] * 10**30,
            collateral_token=account_position['position']['addresses']['collateralToken'],
            pending_funding_fees_usd=int(
                (account_position['fees']['fundingFeeAmount'] * 10**-decimals) * 10**30),
            pending_borrowing_fees_usd=account_position['borrowing']['borrowingFeeUsd'],
            min_collateral_usd=datastore_obj.functions.getUint(min_collateral()).call(),
            is_long=position["is_long"],
            use_max_price_impact=True,
            user_referral_info=None)

        decimals = market_info["market_metadata"]['decimals']

        return liquidation_price / 10**(30 - decimals)

    except Exception as e:
        logger.error(f'GMXGetLiqPrice - Failed to calculate liquidation price for position, symbol = {symbol}. Error: {e}', exc_info=True)
        return None

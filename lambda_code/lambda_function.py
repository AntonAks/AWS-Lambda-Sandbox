import os
from typing import Any

import requests
import hmac
import hashlib
import time
import urllib.parse
from bot import send_telegram_message


class BinanceAPI:
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize the BinanceAPI class with your API key and secret.

        :param api_key: Your Binance API key
        :param api_secret: Your Binance API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"

    def _generate_signature(self, params: dict[str, Any]) -> str:
        """
        Generate a HMAC SHA256 signature for authenticated requests.

        :param params: Dictionary of query parameters
        :return: Signature as a hexadecimal string
        """
        query_string = urllib.parse.urlencode(params)
        return hmac.new(self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    def get_pair_price(self, symbol: str) -> float:
        """
        Fetch the latest price for a given trading pair.

        :param symbol: Trading pair symbol (e.g., "BTCUSDT")
        :return: Price as a float or None if the request fails
        """
        endpoint = "/api/v3/ticker/price"
        url = f"{self.base_url}{endpoint}"

        try:
            # Make a GET request to the Binance API
            response = requests.get(url, params={"symbol": symbol})
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the JSON response
            data = response.json()
            return float(data["price"])  # Convert the price to a float

        except requests.exceptions.RequestException as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None

    def get_account_info(self) -> dict[str, Any]:
        """
        Fetch account information using the Binance API.

        :return: JSON response from the API or None if the request fails
        """
        endpoint = "/api/v3/account"
        url = f"{self.base_url}{endpoint}"

        try:
            # Add timestamp to the request parameters
            params = {
                "timestamp": int(time.time() * 1000)
            }

            # Generate the signature
            params["signature"] = self._generate_signature(params)

            # Make the authenticated request
            headers = {
                "X-MBX-APIKEY": self.api_key
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors

            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error fetching account info: {e}")

    def get_asset_value_in_usd(self, asset: str, amount: float) -> float:
        """
        Calculate the value of an asset in USD.

        :param asset: Asset symbol (e.g., "BTC", "ETH")
        :param amount: Amount of the asset
        :return: Value in USD as a float or None if the price cannot be fetched
        """
        if asset == "USDT":
            return amount  # USDT is already in USD

        # Check if the asset is a "LD" token (e.g., LDETH, LDDOGE)
        if asset.startswith("LD"):
            base_asset = asset[2:]  # Remove the "LD" prefix
            symbol = f"{base_asset}USDT"
        else:
            symbol = f"{asset}USDT"

        # Fetch the price of the asset in USDT
        price = self.get_pair_price(symbol)
        if price is None:
            print(f"Could not fetch price for {symbol}")
            return None

        return price * amount


def lambda_handler(event, context):
    # Initialize the BinanceAPI class
    binance = BinanceAPI(os.environ.get("API_KEY"), os.environ.get("API_SECRET"))

    # Fetch account information
    account_info = binance.get_account_info()
    if account_info is None:
        return {
            "statusCode": 500,
            "body": "Failed to fetch account info"
        }

    # Calculate and print balances
    total_value_usd = 0.0
    result = []

    for balance in account_info["balances"]:
        asset = balance["asset"]
        free = float(balance["free"])
        locked = float(balance["locked"])
        total = free + locked

        if total > 0:  # Only show non-zero balances
            # Calculate the value in USD
            value_usd = binance.get_asset_value_in_usd(asset, total)
            if value_usd is not None:
                total_value_usd += value_usd
                result.append(f"{asset}: Free = {free}, Locked = {locked}, Value = ${value_usd:.2f}")

    result.append(f"\nTotal Portfolio Value: ${total_value_usd:.2f}")

    message = "\n".join(result)

    send_telegram_message(
        os.getenv('BOT_TOKEN'),
        os.getenv('CHATS_LIST').split(','),
        message)

    return {
        "statusCode": 200,
        "message": message
    }

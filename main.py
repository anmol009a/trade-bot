import os
import time
import logging
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceRequestException

# --- 1. Logging Configuration ---
# Logs will be saved to 'trading_bot.log' and printed to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trading_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BasicBot:
    def __init__(self, api_key, api_secret, testnet=True):
        """
        Initialize the Binance Client.
        :param testnet: If True, uses the Binance Futures Testnet.
        """
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            logger.info(f"Bot Initialized. Testnet mode: {testnet}")

            # Verify connection by fetching server time
            self.client.get_server_time()
            logger.info("Connection to Binance API successful.")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise

    def get_account_balance(self, asset='USDT'):
        """Check the balance of a specific asset in Futures wallet."""
        try:
            account = self.client.futures_account()
            for balance in account['assets']:
                if balance['asset'] == asset:
                    return float(balance['walletBalance'])
            return 0.0
        except BinanceAPIException as e:
            logger.error(f"Error fetching balance: {e}")
            return None

    def place_market_order(self, symbol, side, quantity):
        """
        Place a Market Order (Buy/Sell immediately at current price).
        """
        try:
            logger.info(
                f"Attempting MARKET {side} order for {quantity} {symbol}...")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            logger.info(f"Market Order Success: ID {order['orderId']}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error (Market): {e}")
            return None

    def place_limit_order(self, symbol, side, quantity, price):
        """
        Place a Limit Order (Buy/Sell at a specific price).
        """
        try:
            logger.info(
                f"Attempting LIMIT {side} order: {quantity} {symbol} @ {price}...")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,  # Good Till Cancelled
                quantity=quantity,
                price=str(price)
            )
            logger.info(f"Limit Order Success: ID {order['orderId']}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error (Limit): {e}")
            return None

    # --- Bonus: Advanced Order Type ---
    def place_stop_loss_limit(self, symbol, side, quantity, price, stop_price):
        """
        Place a Stop-Loss Limit Order (Advanced).
        Triggers a limit order when the stop_price is hit.
        """
        try:
            logger.info(
                f"Attempting STOP_LOSS_LIMIT {side}: {quantity} {symbol}, Stop: {stop_price}, Limit: {price}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_STOP,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=str(price),
                stopPrice=str(stop_price)
            )
            logger.info(f"Stop-Loss Order Success: ID {order['orderId']}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Binance API Error (Stop-Loss): {e}")
            return None

# --- Helper Functions for CLI ---


def get_user_input(prompt, type_func=str):
    """Helper to validate user input."""
    while True:
        try:
            value = input(prompt)
            return type_func(value)
        except ValueError:
            print("Invalid input format. Please try again.")


def main():
    print("=========================================")
    print("   BINANCE FUTURES TESTNET TRADING BOT   ")
    print("=========================================")

    # 1. Credentials
    # You can hardcode these for testing, but input is safer
    api_key = input("Enter Testnet API Key: ").strip()
    api_secret = input("Enter Testnet API Secret: ").strip()

    if not api_key or not api_secret:
        logger.error("Credentials missing. Exiting.")
        return

    # 2. Initialize Bot
    try:
        # Replace with your Testnet API Key
        bot = BasicBot(api_key, api_secret, testnet=True)
    except Exception:
        print("Initialization failed. Check your API Keys or Internet Connection.")
        return

    # 3. Interactive Loop (Bonus UI)
    while True:
        print("\n--- MENU ---")
        print("1. Check USDT Balance")
        print("2. Place Market Order")
        print("3. Place Limit Order")
        print("4. Place Stop-Loss Limit Order (Bonus)")
        print("5. Exit")

        choice = input("Select an option (1-5): ")

        if choice == '1':
            balance = bot.get_account_balance()
            print(f"Current USDT Balance: {balance}")

        elif choice in ['2', '3', '4']:
            symbol = get_user_input(
                "Enter Symbol (e.g., BTCUSDT): ", str).upper()
            side_input = get_user_input("Side (BUY/SELL): ", str).upper()

            if side_input not in ['BUY', 'SELL']:
                print("Invalid side. Must be BUY or SELL.")
                continue

            qty = get_user_input(f"Enter Quantity for {symbol}: ", float)

            if choice == '2':
                # Market Order
                result = bot.place_market_order(symbol, side_input, qty)
                if result:
                    print(f"Order Executed! Status: {result['status']}")

            elif choice == '3':
                # Limit Order
                price = get_user_input("Enter Limit Price: ", float)
                result = bot.place_limit_order(symbol, side_input, qty, price)
                if result:
                    print(f"Order Placed! Status: {result['status']}")

            elif choice == '4':
                # Stop Loss Order
                price = get_user_input("Enter Limit Price: ", float)
                stop_price = get_user_input(
                    "Enter Trigger (Stop) Price: ", float)
                result = bot.place_stop_loss_limit(
                    symbol, side_input, qty, price, stop_price)
                if result:
                    print(f"Advanced Order Placed! Status: {result['status']}")

        elif choice == '5':
            print("Exiting Bot. Goodbye!")
            break
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()

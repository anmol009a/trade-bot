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
        Initialize the Binance Client and fetch exchange info for precision rules.
        :param testnet: If True, uses the Binance Futures Testnet.
        """
        try:
            self.client = Client(api_key, api_secret, testnet=testnet)
            logger.info(f"Bot Initialized. Testnet mode: {testnet}")

            # Verify connection by fetching server time
            self.client.get_server_time()
            logger.info("Connection to Binance API successful.")

            # Fetch and store exchange info for symbol precision/filters
            self.exchange_info = self.client.futures_exchange_info()
            logger.info(
                "Fetched futures exchange information (for precision checks).")

        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise

    def _get_symbol_filters(self, symbol):
        """Internal method to get filters for a given symbol."""
        for item in self.exchange_info['symbols']:
            if item['symbol'] == symbol:
                return {filter_item['filterType']: filter_item for filter_item in item['filters']}
        raise ValueError(f"Symbol {symbol} not found in exchange information.")

    def _round_value(self, value, step_size_str):
        """Internal method to round a value based on the step size (e.g., 0.001) for API precision."""
        step_size = float(step_size_str)

        # Calculate the number of decimal places in the step_size
        if step_size == 1.0:
            precision = 0
        else:
            # Find precision from stepSize string (e.g., '0.001' -> 3)
            precision = len(step_size_str.split('.')[-1].rstrip('0'))

        # Round the value to the nearest multiple of step_size
        rounded_value = round(value / step_size) * step_size

        # Format to the correct precision string for the API
        return f"{rounded_value:.{precision}f}"

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
        Includes precision rounding.
        """
        try:
            # Apply quantity precision rules
            filters = self._get_symbol_filters(symbol)
            lot_size_filter = filters.get('LOT_SIZE', {})
            qty_step_size = lot_size_filter.get('stepSize', '1')
            rounded_qty = self._round_value(quantity, qty_step_size)

            logger.info(
                f"Attempting MARKET {side} order for {rounded_qty} {symbol}...")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=rounded_qty
            )
            logger.info(f"Market Order Success: ID {order['orderId']}")
            return order
        except (BinanceAPIException, ValueError) as e:
            logger.error(f"Binance API Error (Market): {e}")
            return None

    def place_limit_order(self, symbol, side, quantity, price):
        """
        Place a Limit Order (Buy/Sell at a specific price).
        Includes precision rounding.
        """
        try:
            filters = self._get_symbol_filters(symbol)
            # Apply quantity precision
            lot_size_filter = filters.get('LOT_SIZE', {})
            qty_step_size = lot_size_filter.get('stepSize', '1')
            rounded_qty = self._round_value(quantity, qty_step_size)

            # Apply price precision
            price_filter = filters.get('PRICE_FILTER', {})
            price_tick_size = price_filter.get('tickSize', '1')
            rounded_price = self._round_value(price, price_tick_size)

            logger.info(
                f"Attempting LIMIT {side} order: {rounded_qty} {symbol} @ {rounded_price}...")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,  # Good Till Cancelled
                quantity=rounded_qty,
                price=rounded_price
            )
            logger.info(f"Limit Order Success: ID {order['orderId']}")
            return order
        except (BinanceAPIException, ValueError) as e:
            logger.error(f"Binance API Error (Limit): {e}")
            return None

    # --- Bonus: Advanced Order Type (Stop-Loss Limit) ---
    def place_stop_loss_limit(self, symbol, side, quantity, price, stop_price):
        """
        Place a Stop-Loss Limit Order.
        Triggers a limit order at 'price' when the 'stop_price' is hit.
        Includes precision rounding.
        """
        try:
            filters = self._get_symbol_filters(symbol)
            # Apply quantity precision
            lot_size_filter = filters.get('LOT_SIZE', {})
            qty_step_size = lot_size_filter.get('stepSize', '1')
            rounded_qty = self._round_value(quantity, qty_step_size)

            # Apply price precision (same tick size for limit price and stop price)
            price_filter = filters.get('PRICE_FILTER', {})
            price_tick_size = price_filter.get('tickSize', '1')
            rounded_price = self._round_value(price, price_tick_size)
            rounded_stop_price = self._round_value(stop_price, price_tick_size)

            logger.info(
                f"Attempting STOP_LOSS_LIMIT {side}: {rounded_qty} {symbol}, Stop: {rounded_stop_price}, Limit: {rounded_price}")
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                # This type is used for STOP_MARKET and STOP_LIMIT orders where price is the limit price
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=rounded_qty,
                price=rounded_price,  # This is the limit price that executes once triggered
                stopPrice=rounded_stop_price  # This is the trigger price
            )
            logger.info(f"Stop-Loss Order Success: ID {order['orderId']}")
            return order
        except (BinanceAPIException, ValueError) as e:
            logger.error(f"Binance API Error (Stop-Loss): {e}")
            return None

    def get_open_orders(self, symbol=None):
        """Get all open orders for a specific symbol or all symbols."""
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol)
                logger.info(f"Fetched {len(orders)} open orders for {symbol}.")
            else:
                orders = self.client.futures_get_open_orders()
                logger.info(
                    f"Fetched {len(orders)} open orders across all symbols.")

            if not orders:
                print("No open orders found.")
                return []

            print("\n--- OPEN ORDERS ---")
            for order in orders:
                print(f"ID: {order['orderId']} | Symbol: {order['symbol']} | Side: {order['side']} | Type: {order['type']} | Qty: {float(order['origQty']):.8f} | Price: {float(order['price']):.2f} | Status: {order['status']}")
            print("-------------------")
            return orders

        except BinanceAPIException as e:
            logger.error(f"Error fetching open orders: {e}")
            return None

    def cancel_order_by_id(self, symbol, order_id):
        """Cancel a specific open order by ID."""
        try:
            # Ensure order_id is an integer
            order_id = int(order_id)
            logger.info(
                f"Attempting to cancel order ID {order_id} for {symbol}...")
            result = self.client.futures_cancel_order(
                symbol=symbol, orderId=order_id)
            logger.info(
                f"Order Cancellation Success: ID {result['orderId']}, Status: {result['status']}")
            return result
        except BinanceAPIException as e:
            logger.error(f"Error canceling order ID {order_id}: {e}")
            return None
        except ValueError:
            logger.error("Invalid Order ID. Must be a number.")
            return None

    def cancel_all_open_orders(self, symbol):
        """Cancel all open orders for a specific symbol."""
        try:
            logger.warning(
                f"Attempting to cancel ALL open orders for {symbol}...")
            # futures_cancel_all_open_orders returns a list of orders that were successfully cancelled
            result = self.client.futures_cancel_all_open_orders(symbol=symbol)

            if result['code'] == 200:
                logger.info(
                    f"Successfully cancelled orders for {symbol}.")
            else:
                logger.info(f"No open orders found to cancel for {symbol}.")

            return result
        except BinanceAPIException as e:
            logger.error(f"Error canceling all orders for {symbol}: {e}")
            return None


# --- Helper Functions for CLI ---


def get_user_input(prompt, type_func=str):
    """Helper to validate user input."""
    while True:
        try:
            value = input(prompt)
            # Check for empty input if type is float/int
            if not value and type_func != str:
                raise ValueError("Input cannot be empty.")
            return type_func(value)
        except ValueError:
            print("Invalid input format. Please try again.")


def main():
    print("=========================================")
    print("   BINANCE FUTURES TESTNET TRADING BOT   ")
    print("=========================================")

    # 1. Credentials Input
    print("Please enter your Futures Testnet credentials (NOT Spot or Mainnet keys).")
    api_key = input("Enter Testnet API Key: ").strip()
    api_secret = input("Enter Testnet API Secret: ").strip()

    if not api_key or not api_secret:
        logger.error("Credentials missing. Exiting.")
        return

    # 2. Initialize Bot
    try:
        bot = BasicBot(api_key, api_secret, testnet=True)
    except Exception:
        print("Initialization failed. Check your API Keys or Internet Connection.")
        return

    # 3. Interactive Loop (CLI)
    while True:
        print("\n--- MENU ---")
        print("1. Check USDT Balance")
        print("2. Place Market Order")
        print("3. Place Limit Order")
        print("4. Place Stop-Loss Limit Order (Bonus)")
        print("5. Get Open Orders")
        print("6. Cancel Specific Order by ID")
        print("7. Cancel ALL Open Orders for Symbol")
        print("8. Exit")

        choice = input("Select an option (1-8): ")

        if choice == '1':
            balance = bot.get_account_balance()
            if balance is not None:
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
                price = get_user_input(
                    "Enter Limit Price (executes once triggered): ", float)
                stop_price = get_user_input(
                    "Enter Trigger (Stop) Price: ", float)
                result = bot.place_stop_loss_limit(
                    symbol, side_input, qty, price, stop_price)
                if result:
                    print(f"Advanced Order Placed! Status: {result['status']}")

        elif choice == '5':
            # Get Open Orders
            symbol_input = get_user_input(
                "Enter Symbol (e.g., BTCUSDT) or leave blank for ALL: ", str).upper()
            # If empty string, pass None to function
            bot.get_open_orders(symbol=symbol_input if symbol_input else None)

        elif choice == '6':
            # Cancel Specific Order
            symbol = get_user_input(
                "Enter Symbol (e.g., BTCUSDT): ", str).upper()
            order_id = get_user_input("Enter Order ID to Cancel: ", int)
            bot.cancel_order_by_id(symbol, order_id)

        elif choice == '7':
            # Cancel ALL Orders for Symbol
            symbol = get_user_input(
                "Enter Symbol to Cancel ALL open orders for (e.g., BTCUSDT): ", str).upper()
            confirm = input(
                f"Are you sure you want to cancel ALL open orders for {symbol}? (yes/no): ")
            if confirm.lower() == 'yes':
                bot.cancel_all_open_orders(symbol)
            else:
                print("Cancellation aborted.")

        elif choice == '8':
            print("Exiting Bot. Goodbye!")
            break
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()

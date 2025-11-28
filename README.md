# **🤖 Binance Futures Testnet Trading Bot (Python CLI)**

This project provides a comprehensive, interactive command-line interface (CLI) bot for trading on the **Binance Futures Testnet**.

The bot is built using the official python-binance library and includes essential features like order placement, automatic precision handling, and order management (viewing/cancellation).

## **✨ Features**

* **Secure Initialization:** Connects to the Binance API using your provided Testnet API key and secret.  
* **Futures Market Integration:** Specifically uses the correct endpoints for the Binance Futures platform.  
* **Automatic Precision Handling:** Automatically fetches exchange info and rounds quantity (LOT\_SIZE) and price (PRICE\_FILTER) inputs to the exact precision required by Binance, preventing common API errors.  
* **Core Order Placement:** Supports **MARKET** orders, **LIMIT** orders, and **STOP-LOSS LIMIT** orders.  
* **Order Management:**  
  * Check available **USDT Balance**.  
  * Fetch and display **All Open Orders** for a symbol or all symbols.  
  * **Cancel** a specific order by ID.  
  * **Cancel ALL** open orders for a given symbol.  
* **Robust Logging:** Uses Python's logging module to log all actions and API errors to both the console and a trading\_bot.log file.

## **🛠️ Prerequisites**

Before running the bot, you need:

1. **Python 3.x** installed on your system.  
2. **Binance Futures Testnet API Keys:** You **must** generate API keys specifically for the Testnet environment. Using Mainnet keys will fail. You can generate these keys on the [Binance Futures Testnet Portal](https://testnet.binancefuture.com/).

## **🚀 Setup and Installation**

Follow these steps to set up your trading bot environment:

### **1\. Install Dependencies**

You only need the python-binance library, which handles all communication with the exchange.

pip install python-binance

### **2\. Run the Script**

Save the code provided in the Canvas as a file named binance\_bot.py and run it from your terminal:

python binance\_bot.py

### **3\. Enter Credentials**

The bot will prompt you for your Testnet API Key and Secret when it starts.

**⚠️ IMPORTANT SECURITY NOTE:**

Never share your API keys or store them directly in the code for production environments. For this testing environment, they are entered via command line input.

## **💻 Usage Menu**

Once successfully connected, the bot will present an interactive menu.

| Option | Command | Description |
| :---- | :---- | :---- |
| **1** | Check Balance | Displays your available USDT balance in the Futures Testnet wallet. |
| **2** | Market Order | Executes a BUY or SELL order immediately at the current market price. |
| **3** | Limit Order | Places an order that sits on the order book until the specified price is reached or the order is manually cancelled. |
| **4** | Stop-Loss Limit | Places an advanced order that triggers a limit order when the market hits the specified stop price. |
| **5** | Get Open Orders | Retrieves and lists all active limit/stop orders you currently have open on the exchange. |
| **6** | Cancel Order | Allows you to cancel a single order by providing its unique Order ID. |
| **7** | Cancel ALL Orders | Cancels all open orders for a specified trading symbol (e.g., BTCUSDT). **Use with caution.** |
| **8** | Exit | Closes the bot application. |


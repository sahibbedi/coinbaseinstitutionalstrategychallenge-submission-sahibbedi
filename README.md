# btcbasisdashboard-sahibbedi

<img width="942" height="721" alt="Screenshot 2026-05-27 at 5 57 04 PM" src="https://github.com/user-attachments/assets/1d660a09-57c1-40fc-8f3c-126392db9169" />

# BTC Basis Dashboard: Live Yield & Trade Estimator
A lightweight dashboard that tracks the exact yield of the Bitcoin "cash-and-carry" trade. By pulling live prices for spot Bitcoin and its corresponding futures contract, this tool tells exactly what the trade is paying right now and whether that yield is unusually high or low.

# What Value This Creates
Institutional clients constantly ask about the health of the basis yield. This tool gives them an instant, mathematically precise answer without requiring expensive terminal subscriptions, proprietary data feeds, or API keys. It translates raw, moving prices into a simple "expanding" or "compressing" narrative, allowing users to instantly assess the risk and reward of the trade.

# What the Metrics and Graph Represent
The dashboard is broken down into three core analytical sections:

The Top Snapshot (Live Metrics): This compares the live spot price of Bitcoin against the CME front-month futures contract. The difference between these two prices is converted into a Live Annualised Basis (%).

Note on Market Conditions: If futures are trading higher than spot (contango), the basis is positive, and the trade yields a profit. If futures dip below spot (backwardation)—as seen in periods of extreme volatility or right before a contract expires—the basis turns negative.

90-Day Context: It places today's yield into a historical quartile so you instantly know if the current spread is normal, or in the top/bottom 25% of recent history.

The 30-Day History Chart: A visual trendline tracking the annualized basis over the last month. A rising line means the premium is expanding (getting more profitable); a falling line means the premium is compressing. It provides an immediate visual check on the volatility of the spread.

The Trade Estimator: A practical, built-in calculator. You input your desired position size (Notional) and your cost of capital (Borrow Rate). The engine calculates your exact net annualized yield and estimates your final Profit/Loss on the exact day the futures contract expires.

# How It Works
The app is built entirely in Python and is designed to run anywhere for free.

Data: It uses the yfinance library to permissionlessly fetch public ticker data (BTC-USD and BTC=F).

Math: It relies on pandas and numpy to calculate the exact days to expiry, the rolling averages, and the quartile statistics.

Interface: It uses streamlit to turn the Python script into a clean, interactive web page hosted in the cloud.

# How to Run It Yourself
If you want to run this dashboard outside of the live Streamlit link, you have two options:

Option 1: Run Locally (Interactive Web App)
To run the full visual dashboard on your own machine:

Clone this repository.

Install the simple dependencies:

Bash
pip install -r requirements.txt
Boot the app:

Bash
streamlit run btcbasis.py

Option 2: Test in Google Colab (Text-Based Backup)
If you just want to test the math and data pipelines without setting up a local web environment, use the included Colab notebook.

Open the .ipynb file in this repository via Google Colab.

Run the cells sequentially to fetch the data. It will print a text-based version of the dashboard and render the 30-day history chart directly in your browser.

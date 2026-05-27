import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar

# --- Helper: Calculate Next CME Expiry ---
# CME BTC futures expire on the last Friday of the contract month
def get_next_expiry():
    today = datetime.now()
    last_day = calendar.monthrange(today.year, today.month)[1]
    last_date = datetime(today.year, today.month, last_day)
    offset = (last_date.weekday() - 4) % 7
    last_friday = last_date - timedelta(days=offset)

    if today > last_friday: # If we passed this month's expiry, get next month's
        next_month = today.month + 1 if today.month < 12 else 1
        next_year = today.year if today.month < 12 else today.year + 1
        last_day = calendar.monthrange(next_year, next_month)[1]
        last_date = datetime(next_year, next_month, last_day)
        offset = (last_date.weekday() - 4) % 7
        last_friday = last_date - timedelta(days=offset)

    return last_friday

# --- Data Fetching (Cached for Performance) ---
@st.cache_data(ttl=300) # Refreshes every 5 minutes
def load_data():
    tickers = "BTC-USD BTC=F"
    # Download last 90 days of daily data
    data = yf.download(tickers, period="90d", interval="1d", progress=False)
    # Extract just the Close prices
    df = data['Close'].dropna()
    return df

# --- UI Configuration ---
st.set_page_config(page_title="BTC Basis Dashboard", page_icon="📈", layout="wide")
st.title("Bitcoin Basis Dashboard")
st.markdown("Comparing Spot (`BTC-USD`) vs CME Front-Month Futures (`BTC=F`)")

# --- Main Logic ---
try:
    df = load_data()
    spot = df['BTC-USD']
    futures = df['BTC=F']
except Exception as e:
    st.error("Error fetching data. Yahoo Finance might be rate-limiting.")
    st.stop()

# Calculations
expiry_date = get_next_expiry()
days_to_expiry = max((expiry_date - datetime.now()).days, 1) # Prevent div by zero

# Calculate historical basis (approximate rolling 30-day term for smooth charts)
df['Raw_Basis'] = (df['BTC=F'] / df['BTC-USD']) - 1
df['Ann_Basis_Pct'] = df['Raw_Basis'] * (365 / 30) * 100 

current_spot = spot.iloc[-1]
current_futures = futures.iloc[-1]
current_raw_basis = (current_futures / current_spot) - 1

# Precise annualisation for the live quote based on actual days to expiry
current_ann_basis = current_raw_basis * (365 / days_to_expiry) * 100

# 30-Day and 90-Day Context
basis_30d = df['Ann_Basis_Pct'].tail(30)
basis_90d = df['Ann_Basis_Pct'].tail(90)

avg_30d = basis_30d.mean()
q25 = np.percentile(basis_90d, 25)
q75 = np.percentile(basis_90d, 75)

if current_ann_basis > q75:
    quartile_status = "Top Quartile (Expanding)"
elif current_ann_basis < q25:
    quartile_status = "Bottom Quartile (Compressing)"
else:
    quartile_status = "Middle 50% (Neutral)"

diff_bps = (current_ann_basis - avg_30d) * 100
trend = "expanding" if diff_bps > 0 else "compressing"

# --- Top Level Summary ---
st.info(
    f"**Daily Summary:** Basis is currently **{current_ann_basis:.2f}%** annualised, "
    f"**{abs(diff_bps):.0f} bps** {'above' if diff_bps > 0 else 'below'} its 30-day average, {trend}."
)

# --- Top Metrics Row ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Spot Price", f"${current_spot:,.2f}")
col2.metric("CME Front-Month", f"${current_futures:,.2f}", f"Expires {expiry_date.strftime('%b %d')}")
col3.metric("Live Ann. Basis", f"{current_ann_basis:.2f}%", f"{current_ann_basis - basis_30d.iloc[-2]:.2f}% vs yesterday")
col4.metric("90-Day Context", quartile_status)

st.divider()

# --- Charts and Calculator Row ---
col_chart, col_calc = st.columns([2, 1])

with col_chart:
    st.subheader("30-Day Annualised Basis History")
    st.line_chart(basis_30d)

with col_calc:
    st.subheader("Trade Estimator")
    st.write("Estimate net returns for a cash and carry trade (Long Spot, Short Futures).")
    
    notional = st.number_input("Notional Position ($)", value=100000, step=10000)
    borrow_rate = st.number_input("Annual Financing Rate (%)", value=5.0, step=0.5)

    net_ann_yield = current_ann_basis - borrow_rate
    est_pnl_annual = notional * (net_ann_yield / 100)
    est_pnl_expiry = est_pnl_annual * (days_to_expiry / 365)

    st.markdown(f"**Days to CME Expiry:** {days_to_expiry}")
    st.markdown(f"**Net Annualised Yield:** `{net_ann_yield:.2f}%`")
    
    if net_ann_yield > 0:
        st.success(f"**Estimated PnL (at expiry):** ${est_pnl_expiry:,.2f}")
    else:
        st.error(f"**Estimated PnL (at expiry):** ${est_pnl_expiry:,.2f}")
        
    st.caption(f"*(If held for a full year: ${est_pnl_annual:,.2f})*")

st.caption("Data fetched permissionlessly via Yahoo Finance public API. For educational purposes only.")

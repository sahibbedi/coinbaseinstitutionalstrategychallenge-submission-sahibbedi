import streamlit as st
import yfinance as yf
import pandas as pd
import datetime as dt
import calendar
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="BTC Basis Dashboard", layout="wide")

# --- Helper Functions ---
def get_cme_expiry():
    """Calculates the last Friday of the contract month (CME standard expiry)."""
    today = dt.date.today()
    month_calendar = calendar.monthcalendar(today.year, today.month)
    last_friday = max(week[calendar.FRIDAY] for week in month_calendar)
    expiry = dt.date(today.year, today.month, last_friday)
    
    # If today is past this month's expiry, roll to the next month
    if today >= expiry:
        if today.month == 12:
            month_calendar = calendar.monthcalendar(today.year + 1, 1)
            last_friday = max(week[calendar.FRIDAY] for week in month_calendar)
            expiry = dt.date(today.year + 1, 1, last_friday)
        else:
            month_calendar = calendar.monthcalendar(today.year, today.month + 1)
            last_friday = max(week[calendar.FRIDAY] for week in month_calendar)
            expiry = dt.date(today.year, today.month + 1, last_friday)
            
    days_to_expiry = (expiry - today).days
    return expiry, max(1, days_to_expiry) # Prevent division by zero

@st.cache_data(ttl=300) # Cache for 5 mins to prevent Yahoo Finance rate limits
def fetch_data():
    """Pulls 90 days of spot and futures data to calculate history and quartiles."""
    tickers = ["BTC-USD", "BTC=F"]
    data = yf.download(tickers, period="90d", interval="1d", progress=False)['Close']
    data = data.dropna()
    return data

# --- Main App ---
st.title("📊 BTC Basis Dashboard")
st.markdown("Live yield tracking and trade estimation for the Bitcoin cash-and-carry trade.")

try:
    # 1. Fetch Data & Expiry
    df = fetch_data()
    expiry_date, days_to_expiry = get_cme_expiry()
    
    # 2. Process Live Metrics
    latest_spot = df['BTC-USD'].iloc[-1]
    latest_fut = df['BTC=F'].iloc[-1]
    
    # Live Annualized Basis = ((Futures / Spot) - 1) * (365 / Days to Expiry)
    live_basis_pct = ((latest_fut / latest_spot) - 1) * (365 / days_to_expiry) * 100
    
    # Process Historical Basis for the Chart & Quartiles
    df['Ann_Basis'] = ((df['BTC=F'] / df['BTC-USD']) - 1) * (365 / days_to_expiry) * 100
    hist_30d = df['Ann_Basis'].tail(30)
    
    # Quartile Math
    q75 = df['Ann_Basis'].quantile(0.75)
    q25 = df['Ann_Basis'].quantile(0.25)
    
    if live_basis_pct >= q75:
        context = "🟢 Top Quartile (Expanding)"
    elif live_basis_pct <= q25:
        context = "🔴 Bottom Quartile (Compressing)"
    else:
        context = "🟡 Middle 50% (Normal)"

    # --- UI: Top Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Spot Price (BTC-USD)", f"${latest_spot:,.2f}")
    col2.metric("Front-Month (BTC=F)", f"${latest_fut:,.2f}", f"Expires {expiry_date.strftime('%b %d')}")
    col3.metric("Live Ann. Basis", f"{live_basis_pct:.2f}%")
    col4.metric("90-Day Context", context)
    
    st.divider()

    # --- UI: Layout for Chart and Estimator ---
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("30-Day Annualised Basis History")
        # Build an interactive Plotly chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_30d.index, 
            y=hist_30d.values,
            mode='lines',
            line=dict(color='#1D3557', width=3),
            name="Ann. Basis (%)"
        ))
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            yaxis_title="Annualised Basis (%)",
            plot_bgcolor='white',
            hovermode="x unified"
        )
        fig.update_yaxes(gridcolor='rgba(0,0,0,0.1)')
        st.plotly_chart(fig, use_container_width=True)

    with right_col:
        st.subheader("🧮 Trade Estimator")
        st.markdown("Calculate the net yield of holding the trade through expiry.")
        
        # Interactive Inputs
        notional = st.number_input("Notional Position Size ($)", value=100000.0, step=10000.0)
        borrow_rate = st.number_input("Cost of Capital / Borrow Rate (%)", value=5.0, step=0.5)
        
        # Estimator Math
        net_ann_yield = live_basis_pct - borrow_rate
        absolute_yield = net_ann_yield * (days_to_expiry / 365)
        est_pnl = notional * (absolute_yield / 100)
        
        # Output Results
        st.info(f"**Days to Expiry:** {days_to_expiry}")
        
        if net_ann_yield > 0:
            st.success(f"**Net Ann. Yield:** {net_ann_yield:.2f}%\n\n**Est. PnL at Expiry:** ${est_pnl:,.2f}")
        else:
            st.error(f"**Net Ann. Yield:** {net_ann_yield:.2f}%\n\n**Est. PnL at Expiry:** ${est_pnl:,.2f}")
            
except Exception as e:
    st.error(f"Error loading data from Yahoo Finance. The API may be rate-limiting. Please try again in a few minutes. (Error: {e})")

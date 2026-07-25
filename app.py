import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. SET UP THE APP INTERFACE ---
st.title("📈 Statistical Prediction & Entry Dashboard")
st.markdown("This free app looks at market trends to predict up/down momentum.")

# Sidebar for User Inputs
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Enter Index/Stock Ticker:", "SPY").upper()
timeframe = st.sidebar.selectbox("Select Time Frame:", ["1d", "1h", "15m", "5m"])

# --- 2. GET THE FREE DATA (BUG-FIXED!) ---
@st.cache_data
def load_data(ticker_symbol, interval):
    # Determine how many days of data to pull based on timeframe to stay within free limits
    period = "1mo" if interval in ["15m", "5m", "1h"] else "2y"
    
    # Download data from Yahoo Finance
    data = yf.download(tickers=ticker_symbol, period=period, interval=interval, progress=False)
    
    # ---> YFINANCE BUG FIX: Flatten messy stacked columns <---
    if isinstance(data.columns, pd.MultiIndex):
        # Forces pandas to just use basic names ('Close', 'High', etc.)
        data.columns = data.columns.get_level_values(0) 
        
    return data

st.write(f"Fetching {timeframe} live data for {ticker}...")
df = load_data(ticker, timeframe)

if not df.empty:
    # --- 3. THE MATH & PATTERN RECOGNITION (The "Brain") ---
    # Calculate Simple Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # Calculate basic Relative Strength Index (RSI) manually
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df = df.dropna() # Remove empty rows so we don't trip up

    # --- 4. THE PREDICTION LOGIC ---
    last_row = df.iloc[-1].copy()
    
    # Ensure our SMA columns evaluate to pure scalar float numbers, not messy Series 
    sma20 = float(last_row['SMA_20'])
    sma50 = float(last_row['SMA_50'])
    rsi = float(last_row['RSI'])
    curr_close = float(last_row['Close'])
    
    signal = "NEUTRAL"
    confidence = 0
    
    if sma20 > sma50:
        signal = "⬆️ LIKELY UP"
        confidence += 40
        if 50 < rsi < 70:
             confidence += 35 # Healthy momentum
    elif sma20 < sma50:
        signal = "⬇️ LIKELY DOWN"
        confidence += 40
        if 30 < rsi < 50:
             confidence += 35 # Healthy downward momentum
            
    # Oversold / Overbought reversal signals override standard momentum
    if rsi >= 75:
        signal = "⬇️ REVERSAL RISK (DOWN)"
        confidence = 80
    elif rsi <= 25:
         signal = "⬆️ REVERSAL RISK (UP)"
         confidence = 80

    # --- 5. SHOW REAL-TIME UI RESULTS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${curr_close:.2f}")
    col2.metric("Prediction / Signal", signal)
    col3.metric("Signal Confidence", f"{confidence}%")

    st.subheader(f"Current RSI is: {rsi:.2f}")

    # Show raw historical statistics in a nice table
    st.write("Recent Market Statistics Data:")
    st.dataframe(df[['Close', 'SMA_20', 'SMA_50', 'RSI']].tail())
    
    # Line chart using Streamlit's built-in chart
    st.line_chart(df[['Close', 'SMA_20', 'SMA_50']])
    
else:
    st.error("Could not grab data. Check ticker symbol or internet connection.")

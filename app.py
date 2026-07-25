import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. SET UP THE APP INTERFACE ---
st.title("📈 Statistical Prediction & Entry Dashboard")
st.markdown("This free app looks at market trends to predict up/down momentum.")

# Sidebar for User Inputs
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Enter Index/Stock Ticker:", "SPY")
timeframe = st.sidebar.selectbox("Select Time Frame:", ["1d", "1h", "15m", "5m"])

# --- 2. GET THE FREE DATA ---
@st.cache_data
def load_data(ticker_symbol, interval):
    # Determine how many days of data to pull based on timeframe to stay within free limits
    period = "1mo" if interval in ["15m", "5m", "1h"] else "2y"
    
    # Download data from Yahoo Finance
    data = yf.download(tickers=ticker_symbol, period=period, interval=interval)
    return data

st.write(f"Fetching {timeframe} live data for {ticker}...")
df = load_data(ticker, timeframe)

if not df.empty:
    # --- 3. THE MATH & PATTERN RECOGNITION (The "Brain") ---
    # Calculate Simple Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    # Calculate basic Relative Strength Index (RSI) manually for free
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df = df.dropna() # Remove empty rows

    # --- 4. THE PREDICTION LOGIC ---
    last_row = df.iloc[-1]
    
    # Let's write our statistical rules!
    signal = "NEUTRAL"
    confidence = 0
    
    if last_row['SMA_20'] > last_row['SMA_50']:
        signal = "⬆️ LIKELY UP"
        confidence += 40
        if last_row['RSI'] > 50 and last_row['RSI'] < 70:
             confidence += 35 # Healthy momentum
    elif last_row['SMA_20'] < last_row['SMA_50']:
        signal = "⬇️ LIKELY DOWN"
        confidence += 40
        if last_row['RSI'] < 50 and last_row['RSI'] > 30:
             confidence += 35 # Healthy downward momentum
            
    # Oversold / Overbought reversal signals
    if last_row['RSI'] >= 75:
        signal = "⬇️ REVERSAL RISK (DOWN)"
        confidence = 80
    elif last_row['RSI'] <= 25:
         signal = "⬆️ REVERSAL RISK (UP)"
         confidence = 80

    # --- 5. SHOW REAL-TIME UI RESULTS ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${last_row['Close']:.2f}")
    col2.metric("Prediction / Signal", signal)
    col3.metric("Signal Confidence", f"{confidence}%")

    st.subheader(f"Current RSI is: {last_row['RSI']:.2f}")

    # Show raw historical statistics in a nice table
    st.write("Recent Market Statistics Data:")
    st.dataframe(df[['Close', 'SMA_20', 'SMA_50', 'RSI']].tail())
    
    # Optional line chart using streamlit's built-in chart
    st.line_chart(df[['Close', 'SMA_20', 'SMA_50']])
    
else:
    st.error("Could not grab data. Check ticker symbol or internet connection.")

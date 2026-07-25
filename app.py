import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. SET UP THE APP INTERFACE ---
st.set_page_config(layout="wide") # Use wide screen mode for better charts
st.title("📈 Quant Momentum & Volatility App")
st.markdown("Advanced Dashboard using MACD, Standard Deviations (Bollinger), and RSI.")

st.sidebar.header("Scan Parameters")
ticker = st.sidebar.text_input("Enter Ticker (e.g. SPY, AAPL, BTC-USD):", "SPY").upper()
timeframe = st.sidebar.selectbox("Select Time Frame:", ["1d", "1h", "15m", "5m"])

# --- 2. DATA PULL (With Multi-Index Fix) ---
@st.cache_data
def load_data(ticker_symbol, interval):
    period = "1mo" if interval in ["15m", "5m", "1h"] else "2y"
    data = yf.download(tickers=ticker_symbol, period=period, interval=interval, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0) 
    return data

df = load_data(ticker, timeframe)

if not df.empty and len(df) > 35:
    # --- 3. ADVANCED QUANT MATHEMATICS ---
    
    # A. Volatility: Bollinger Bands (2 Standard Deviations)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    rolling_std = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['SMA_20'] + (rolling_std * 2)
    df['Lower_Band'] = df['SMA_20'] - (rolling_std * 2)

    # B. Momentum: MACD (Moving Average Convergence Divergence)
    ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # C. Oscillators: Standard RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df = df.dropna()

    # --- 4. CONFLUENCE PREDICTION LOGIC ---
    last_row = df.iloc[-1].copy()
    
    # Force convert to pure python floats for absolute stability
    curr_close = float(last_row['Close'])
    upper_bb = float(last_row['Upper_Band'])
    lower_bb = float(last_row['Lower_Band'])
    macd = float(last_row['MACD'])
    macd_sig = float(last_row['MACD_Signal'])
    rsi = float(last_row['RSI'])
    
    # We look for "Confluence" (Multiple indicators agreeing)
    signal = "NEUTRAL"
    confidence = 0
    
    # Check Reversals first (Are we violently outside statistical bands?)
    if curr_close >= upper_bb:
        signal = "🔥 DANGER: Overbought Reversal Imminent (DOWN)"
        confidence = 90
    elif curr_close <= lower_bb:
        signal = "🚀 DANGER: Oversold Bounce Imminent (UP)"
        confidence = 90
        
    # If inside bands, evaluate trend direction via MACD
    else:
        if macd > macd_sig: # Bullish Momentum Cross
            signal = "⬆️ LIKELY UP"
            confidence += 45
            if 50 < rsi < 70: confidence += 20 # Add healthy RSI validation
        elif macd < macd_sig: # Bearish Momentum Cross
            signal = "⬇️ LIKELY DOWN"
            confidence += 45
            if 30 < rsi < 50: confidence += 20
            
    # --- 5. RENDER THE PROFESSIONAL DASHBOARD ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Price", f"${curr_close:.2f}")
    col2.metric("System Signal", signal)
    col3.metric("System Confidence", f"{confidence}%")
    col4.metric("RSI Score", f"{rsi:.1f}")

    st.markdown("---")
    
    # --- INTERACTIVE CANDLESTICK CHART ---
    st.subheader(f"{ticker} Technical Chart")
    
    chart_df = df.tail(100) # Only chart the most recent 100 periods so it looks clean
    
    fig = go.Figure(data=[go.Candlestick(x=chart_df.index,
                    open=chart_df['Open'], high=chart_df['High'],
                    low=chart_df['Low'], close=chart_df['Close'],
                    name="Price Action")])
                    
    # Plotting our Volatility Bands
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Upper_Band'], mode='lines', name='Upper Bollinger (Short Zone)', line=dict(color='rgba(255, 0, 0, 0.4)', dash='dot')))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['Lower_Band'], mode='lines', name='Lower Bollinger (Buy Zone)', line=dict(color='rgba(0, 255, 0, 0.4)', dash='dot')))
    
    fig.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # Let the user peek at the hard statistics logic
    st.write("📊 Live Algorithmic Status (Last Bar Check)")
    stat_data = {
        "Metric": ["Price relative to upper band", "Price relative to lower band", "MACD Histogram (Momentum)"],
        "Value": [f"{(upper_bb - curr_close):.2f} pts away", f"{(curr_close - lower_bb):.2f} pts away", f"{(macd - macd_sig):.2f}"]
    }
    st.dataframe(stat_data)

else:
    st.error(f"Waiting for market data, or symbol not found.")

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. APP SETUP ---
st.set_page_config(layout="wide")
st.title("🏦 Institutional Smart Money (ICT) Algorithm")
st.markdown("Advanced Price Action tracker analyzing Order Flow, Liquidity, and Imbalances instead of lagging retail math.")

st.sidebar.header("Smart Money Setup")
ticker = st.sidebar.text_input("Enter Ticker:", "SPY").upper()
timeframe = st.sidebar.selectbox("Select Time Frame:", ["15m", "1h", "1d"])

# --- 2. DATA PULL & FIX ---
@st.cache_data
def load_data(ticker_symbol, interval):
    period = "60d" if interval in ["15m", "1h"] else "2y"
    data = yf.download(tickers=ticker_symbol, period=period, interval=interval, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0) 
    return data

df = load_data(ticker, timeframe)

if not df.empty and len(df) > 50:
    # --- 3. ICT & SMC ALGORITHMIC LOGIC (NO INDICATORS) ---
    
    # 1. Premium & Discount Array (Determine the Institutional Trade Zone)
    # We look at the macro swing (last 50 periods)
    macro_high = df['High'].tail(50).max()
    macro_low = df['Low'].tail(50).min()
    equilibrium = (macro_high + macro_low) / 2
    
    # 2. Fair Value Gaps (Imbalance/Voids that attract price mathematically)
    # A Bullish FVG occurs if Low of candle 'n' > High of candle 'n-2' 
    df['Bull_FVG'] = df['Low'] > df['High'].shift(2)
    # A Bearish FVG occurs if High of candle 'n' < Low of candle 'n-2'
    df['Bear_FVG'] = df['High'] < df['Low'].shift(2)
    
    # 3. Target Liquidity (Buy Side and Sell Side Puddles - Retail Stop Losses)
    # Looking for pivot points where massive pending orders are sitting
    df['BSL'] = df['High'].rolling(10).max().shift(1)  # Buy Side Liquidity (Swing Highs)
    df['SSL'] = df['Low'].rolling(10).min().shift(1)   # Sell Side Liquidity (Swing Lows)
    
    # --- 4. PRICE PREDICTION & ACTION GENERATOR ---
    last_row = df.iloc[-1]
    curr_close = float(last_row['Close'])
    curr_low = float(last_row['Low'])
    curr_high = float(last_row['High'])
    ssl_target = float(last_row['SSL'])
    bsl_target = float(last_row['BSL'])

    # Institutional rules mandate action ONLY in valid pricing models
    zone_state = "PREMIUM (NO BUY ZONE)" if curr_close > equilibrium else "DISCOUNT (NO SELL ZONE)"
    color_state = "red" if zone_state.startswith("PREM") else "green"

    signal = "NEUTRAL 😴 (Wait for manipulation...)"
    details = "Waiting for retail to set structural liquidity lines."
    
    # Algorithmic Conditions based on ICT/SMC 
    if curr_close < equilibrium: # IN DISCOUNT
        if curr_low < ssl_target:
             signal = "🔥 SMC BUY SIGNAL: SELL SIDE SWEPT"
             details = "Turtle Soup Play: Stop-losses hunted in Discount. Large buy side probability initiated!"
        elif curr_close < (equilibrium - ((equilibrium-macro_low)*0.7)):
             signal = "🟢 HIGH-CONVICTION DISCOUNT ACCUMULATION"
             details = "Deep Discount (Oversold Structurally). Institutional Buys Highly Likely."

    elif curr_close > equilibrium: # IN PREMIUM
        if curr_high > bsl_target:
             signal = "🚨 SMC SELL SIGNAL: BUY SIDE SWEPT"
             details = "Liquidity Run: Short positions being engineered above previous highs in a Premium Zone."

    # --- 5. RENDER REAL-TIME INTERFACE ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Target Price", f"${curr_close:.2f}")
    col2.metric("ICT Bias Zone", zone_state)
    col3.metric("Buy Side Liquidity Target", f"${bsl_target:.2f}")
    col4.metric("Sell Side Liquidity Target", f"${ssl_target:.2f}")

    # Visualizing Institutional Logic
    st.subheader(signal)
    st.markdown(details)
    st.markdown("---")
    
    st.subheader(f"📊 SMC Raw Footprint / ICT Setup: {ticker}")
    chart_df = df.tail(80) # Last 80 candles so market structure looks clear

    fig = go.Figure()
    
    # Plot Standard Price Candles
    fig.add_trace(go.Candlestick(x=chart_df.index,
                                 open=chart_df['Open'], high=chart_df['High'],
                                 low=chart_df['Low'], close=chart_df['Close'],
                                 name="Raw Price"))
                                 
    # Plot Liquidity Sweep Lines (Retail Traps)
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['BSL'], 
                             mode='lines', line=dict(color='yellow', dash='dot', width=1.5), 
                             name='Buy-Side Liquidity (Resistance Pool)'))
    fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df['SSL'], 
                             mode='lines', line=dict(color='yellow', dash='dot', width=1.5), 
                             name='Sell-Side Liquidity (Support Pool)'))
    
    # Add Premium and Discount Block visualization 
    fig.add_hrect(y0=macro_low, y1=equilibrium, fillcolor="rgba(0,255,0,0.1)", 
                  layer="below", line_width=0, name="Discount Accumulation")
    fig.add_hrect(y0=equilibrium, y1=macro_high, fillcolor="rgba(255,0,0,0.1)", 
                  layer="below", line_width=0, name="Premium Distribution")

    # Add 50% Equilibrium strict dividing line
    fig.add_trace(go.Scatter(x=chart_df.index, y=[equilibrium]*len(chart_df), 
                             mode='lines', line=dict(color='white', width=1), 
                             name='Equilibrium (0.5 Zone)'))

    # Dark background formatting with no rangeslider junk
    fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_dark",
                      margin=dict(l=0, r=0, t=20, b=0), showlegend=True,
                      legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Missing Data!")

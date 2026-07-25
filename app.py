import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. CORE CONFIGURATION ---
st.set_page_config(layout="wide")
st.title("🧮 Institutional Liquidity Sweep Engine")
st.markdown("Raw data logic prioritizing Fractal Structure Sweeps with strict >3:1 Risk constraints.")

col1, col2 = st.sidebar.columns(2)
ticker = col1.text_input("Ticker:", "BTC-USD").upper()
timeframe = col2.selectbox("Frame:", ["5m", "15m", "1h", "1m"])

# --- 2. FAST MARKET DATA FETCH ---
@st.cache_data(ttl=30)
def load_order_flow(ticker_symbol, interval):
    if interval == "1m": period = "5d"
    elif interval in ["5m", "15m"]: period = "20d"
    else: period = "2y"
    
    # Grab most recent market data instantly 
    df = yf.download(tickers=ticker_symbol, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
         df.columns = df.columns.get_level_values(0) 
    return df

with st.spinner("Compiling order flow footprints..."):
    df = load_order_flow(ticker, timeframe)

if not df.empty and len(df) > 50:
    # --- 3. HARDCORE MATH & SMC FRACTALS (No Indicators) ---
    df = df.dropna().copy()
    
    # Mathematical Swing Matrix to identify Major Liquidity Pools
    # Look back 15 candles and look forward 15 candles to ensure true pivot dominance
    pivot_length = 15 
    
    df['Fractal_High'] = df['High'][df['High'] == df['High'].rolling(window=(pivot_length*2)+1, center=True).max()]
    df['Fractal_Low'] = df['Low'][df['Low'] == df['Low'].rolling(window=(pivot_length*2)+1, center=True).min()]
    
    # Fill forwards to establish current horizontal critical thresholds (Important Levels)
    df['Active_BSL'] = df['Fractal_High'].ffill() 
    df['Active_SSL'] = df['Fractal_Low'].ffill()

    # Determine structural bias (Macro) via past 50 period equilibrium 
    recent_range_high = df['High'].tail(50).max()
    recent_range_low = df['Low'].tail(50).min()
    equilibrium = (recent_range_high + recent_range_low) / 2
    
    # --- 4. THE LIQUIDITY TRAP & RR (RISK/REWARD) CALCULATION ---
    # Slice off the exact last complete sequence 
    current_idx = df.index[-1]
    curr_data = df.iloc[-1]
    
    c_close = float(curr_data['Close'])
    c_high = float(curr_data['High'])
    c_low = float(curr_data['Low'])
    
    # Fetch Important Levels that are nearest active
    nearest_bsl = float(curr_data['Active_BSL'])
    nearest_ssl = float(curr_data['Active_SSL'])
    
    signal = "NEUTRAL: Seeking Liquidity Engagements"
    status_code = "grey"
    
    trade_exec = False
    direction = ""
    entry = 0.0
    sl = 0.0
    tp = 0.0
    
    # Filter 1: LONG ENTRY CALCULATION (SELL SIDE SWEEP)
    # Price pierced the support SSL liquidity (took out retailers), but has rapidly reversed above it.
    if (c_low < nearest_ssl) and (c_close > nearest_ssl) and (c_close < equilibrium):
        signal = "🚨 SMC BUY ENGINE EXECUTED: TURTLE SOUP SELL-SIDE SWEEP"
        status_code = "green"
        direction = "LONG"
        
        entry = c_close 
        sl_buffer = (entry * 0.0005) # Half a tenth percent dynamic buffer for market makers pushing limit spreads
        sl = c_low - sl_buffer # Safety line strictly beneath the aggressive institutional trap wick
        
        # MATH LIMITS: R/R constraint formulation 
        risk_per_share = entry - sl
        target_reward = risk_per_share * 3.0 # Hard lock on 3R calculation minimum
        tp = entry + target_reward
        trade_exec = True

    # Filter 2: SHORT ENTRY CALCULATION (BUY SIDE SWEEP)
    # Price wick sweeps premium retail High stops (BSL), but candle bodies crush backwards. 
    elif (c_high > nearest_bsl) and (c_close < nearest_bsl) and (c_close > equilibrium):
        signal = "🚨 SMC SELL ENGINE EXECUTED: TURTLE SOUP BUY-SIDE SWEEP"
        status_code = "red"
        direction = "SHORT"
        
        entry = c_close 
        sl_buffer = (entry * 0.0005) 
        sl = c_high + sl_buffer
        
        risk_per_share = sl - entry
        target_reward = risk_per_share * 3.0
        tp = entry - target_reward
        trade_exec = True


    # --- 5. RENDER PURE EXECUTABLE DATA ---
    st.markdown(f"### Real-time Matrix Bias: `{ticker} [{timeframe}]`")
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Action Output", f"${c_close:,.2f}")
    col2.metric("Important Level: Resist. (BSL)", f"${nearest_bsl:,.2f}")
    col3.metric("Important Level: Support (SSL)", f"${nearest_ssl:,.2f}")

    if trade_exec:
        if direction == "LONG":
            st.success(f"{signal}")
            st.write("Retail support liquidated and immediately snapped upwards by volume.")
        else:
            st.error(f"{signal}")
            st.write("Retail upside breakouts were trapped, pushing short structures.")

        # --- EXACT EXECUTION BLOCKS ---
        st.markdown(f"### 🔥 TRADE METRICS GENERATED")
        r_cols = st.columns(4)
        
        # We output pure order parameters needed for placing live ticket setups 
        r_cols[0].metric(label="Direction", value=direction)
        r_cols[1].metric(label="Action Point (Entry)", value=f"${entry:,.4f}")
        r_cols[2].metric(label="Safety Void (SL) - Under Wick", value=f"${sl:,.4f}", delta="In-market risk mapping")
        r_cols[3].metric(label="Alpha Extraction (TP) - Fixed >3:1", value=f"${tp:,.4f}", delta="Required 3R math generated")
        
        st.write("#### Data Audit (RR Configuration Validation)")
        dist_risk = abs(entry - sl)
        dist_tp = abs(entry - tp)
        ratio_verify = dist_tp / dist_risk if dist_risk > 0 else 0 
        st.text(f">> Mathematical Absolute Risk / Return Configuration Audit:")
        st.text(f"      Spread Distance at risk : {dist_risk:,.5f} units per share/contract")
        st.text(f"      Calculated Exit yield   : {dist_tp:,.5f} units per share/contract")
        st.text(f"      Live System Yield R-Calc: {ratio_verify:.2f}:1")
    else:
        st.info("Scanner Engine Iterating Data. Zero edge criteria satisfied for entry execution.")
        st.write("Patience mechanism active: Holding fire for structural stop sweeps of liquidity parameters detailed in Matrix block above. Only extreme deviations will generate setup code.")
        
    st.markdown("---")
    # Output Raw Logic Validation Engine Table to prove no hidden lag indicators were used 
    st.write("##### Raw Market Mechanics Data Terminal")
    audit_df = df[['Open','High','Low','Close','Active_SSL','Active_BSL']].tail(10)
    st.dataframe(audit_df.iloc[::-1]) # Flips frame so newest tick rests cleanly at index top

else:
    st.error("No raw flow recorded for specific parameters.")

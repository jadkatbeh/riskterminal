import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf
import plotly.graph_objects as go

# Configure Streamlit page settings for a full-width institutional-style dashboard
st.set_page_config(page_title="Hedge Fund Risk Terminal", layout="wide")

# --- APPLICATION HEADER / TERMINAL TITLE ---
st.title("Institutional Risk & Stress Terminal")
st.markdown("### Portfolio Solvency & Value at Risk (VaR) Engine")
st.divider()

# --- USER INPUT PANEL: PORTFOLIO CONSTRUCTION ---
# Sidebar allows users to define the portfolio assets and risk parameters
st.sidebar.header("Portfolio Configuration")
tickers_input = st.sidebar.text_input("Enter Assets (comma separated)", "SPY, QQQ, TSLA, BTC-USD")
initial_investment = st.sidebar.number_input("Portfolio Value ($)", 100000, 10000000, 1000000)
confidence_level = st.sidebar.slider("Confidence Level (%)", 90, 99, 95)

# --- DATA PREPARATION ---
# Convert comma-separated asset input into a cleaned list of ticker symbols
tickers = [t.strip().upper() for t in tickers_input.split(",")]

if st.button("EXECUTE QUANTITATIVE STRESS TEST"):
    with st.spinner("Analyzing Global Market Covariance..."):
        
        # 1. DATA ACQUISITION
        # Download 1 year of historical closing price data for the selected assets
        data = yf.download(tickers, period="1y")['Close']
        returns = data.pct_change().dropna()
        
        # 2. PORTFOLIO RETURN CALCULATION
        # Construct an equal-weight portfolio and compute daily portfolio returns
        weights = np.array([1/len(tickers)] * len(tickers)) # Equal weighted for now
        port_returns = returns.dot(weights)
        
        # Calculate cumulative returns and core portfolio statistics
        cumulative_returns = (1 + port_returns).cumprod()
        total_return = (cumulative_returns.iloc[-1] - 1) * 100
        ann_vol = port_returns.std() * np.sqrt(252)
        sharpe = (port_returns.mean() / port_returns.std()) * np.sqrt(252)

        # 3. VALUE AT RISK (VaR) ESTIMATION
        # Estimate parametric Value at Risk using the empirical return distribution
        var_percentile = np.percentile(port_returns, 100 - confidence_level)
        potential_loss = initial_investment * var_percentile

        # --- PERFORMANCE METRICS DISPLAY ---
        # Display key institutional portfolio metrics in a dashboard format
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Annual Return", f"{total_return:.2f}%")
        col2.metric("Annualized Volatility", f"{ann_vol*100:.2f}%")
        col3.metric("Sharpe Ratio", f"{sharpe:.2f}")
        col4.metric(f"VaR ({confidence_level}%)", f"${abs(potential_loss):,.2f}", delta="-Potential Loss", delta_color="inverse")

        # --- HISTORICAL PERFORMANCE VISUALIZATION ---
        # Plot portfolio equity curve to visualize historical performance and drawdowns
        st.subheader("Historical Drawdown & Performance")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cumulative_returns.index, y=cumulative_returns, name="Portfolio Performance", line=dict(color='#00FFCC')))
        fig.update_layout(template="plotly_dark", title="Equity Curve (1Y Historical)")
        st.plotly_chart(fig, use_container_width=True)

        # --- MONTE CARLO RISK SIMULATION ---
        # Simulate potential future portfolio paths using geometric Brownian motion
        st.subheader("1,000 Path Monte Carlo Simulation")
        simulations = 1000
        days = 252
        dt = 1/252
        
        last_price = initial_investment
        simulation_df = pd.DataFrame()

        # Generate simulated price trajectories based on historical return statistics
        for x in range(simulations):
            prices = [last_price]
            for _ in range(days):
                prices.append(prices[-1] * np.exp((port_returns.mean() - 0.5 * port_returns.std()**2) * dt + 
                              port_returns.std() * np.sqrt(dt) * np.random.normal()))
            simulation_df[x] = prices

        # Plot simulated portfolio value distributions
        fig_sim = px.line(simulation_df, title=f"Future 1-Year Probability Paths for {tickers_input}", labels={'value': 'Portfolio Value', 'index': 'Trading Days'})
        fig_sim.update_layout(showlegend=False, template="plotly_dark")
        st.plotly_chart(fig_sim, use_container_width=True)
        
        # Final interpretation of Value at Risk for user readability
        st.success(f"**Analysis Complete:** Your portfolio has a {100-confidence_level}% chance of losing more than ${abs(potential_loss):,.2f} in a single day.")
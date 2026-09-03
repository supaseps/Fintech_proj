import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from indicators import (
    stock_picker,
    moving_average_calculator,
    relative_strength_index,
    get_earning_date,
    get_pe,
    get_price_target,
)


def compute_adx(data, period=14):
    """
    Vectorized ADX / +DMI / -DMI, computed locally so test.py doesn't depend on
    indicators.py's Average_Directional_Index (which seeds its iterative smoothing
    loop before the +/-DMI series actually have their first valid value, causing
    the ADX column to lock into NaN for every row from that point on).
    Uses Wilder's smoothing via .ewm(alpha=1/period, adjust=False), which is
    mathematically the same recursive formula but doesn't rely on manual
    row-by-row assignment, so there's no seed-alignment bug and no risk of
    pandas silently dropping the write under copy-on-write semantics.
    """
    high, low, close = data["High"], data["Low"], data["Close"]
    prev_close = close.shift(1)

    true_range = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=data.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=data.index)

    atr = true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    plus_dm_smooth = plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    minus_dm_smooth = minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    plus_dmi = 100 * (plus_dm_smooth / atr)
    minus_dmi = 100 * (minus_dm_smooth / atr)
    dx = 100 * (plus_dmi - minus_dmi).abs() / (plus_dmi + minus_dmi)
    adx = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    latest_adx = adx.iloc[-1]
    if pd.isna(latest_adx):
        signal = "ADX is not available because there is insufficient data."
    elif latest_adx < 20:
        signal = "Weak trend / sideways market"
    elif latest_adx < 25:
        signal = "Trend may be starting"
    elif latest_adx < 50:
        signal = "Strong trend"
    elif latest_adx < 75:
        signal = "Very strong trend"
    else:
        signal = "Extremely strong trend"

    return adx, plus_dmi, minus_dmi, signal

st.set_page_config(page_title="Stock Technical Analysis", layout="wide")
st.title("Stock Indicator Analysis")

# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "stock" not in st.session_state:
    st.session_state.stock = None
if "data" not in st.session_state:
    st.session_state.data = None
if "active_indicators" not in st.session_state:
    st.session_state.active_indicators = []  # list of strings, e.g. ["RSI", "ADX", "MA"]

INDICATOR_OPTIONS = {
    "ADX": "ADX with +DMI / -DMI",
    "RSI": "RSI",
    "MA": "Short & Long Term Moving Average (SMA50 / SMA200)",
}

# ---------------------------------------------------------------------------
# Ticker entry
# ---------------------------------------------------------------------------
ticker_input = st.text_input("Enter a stock ticker", value="AAPL").strip().upper()

if st.button("Load Stock"):
    if not ticker_input:
        st.warning("Please enter a ticker symbol.")
    else:
        with st.spinner(f"Fetching data for {ticker_input}..."):
            picker_result = stock_picker(ticker_input)

        if picker_result is None:
            st.error(f"No stock found for ticker '{ticker_input}'.")
            st.session_state.stock = None
            st.session_state.data = None
        else:
            stock, data = picker_result

            # Newer yfinance versions return MultiIndex columns (e.g. ("Close", "AAPL"))
            # even for a single ticker. indicators.py expects flat columns like "Close",
            # so normalize here without touching indicators.py.
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            st.session_state.stock = stock
            st.session_state.data = data
            st.session_state.active_indicators = []  # reset add-ons for the new stock

# ---------------------------------------------------------------------------
# Main body — only render once a stock is loaded
# ---------------------------------------------------------------------------
if st.session_state.data is not None:
    stock = st.session_state.stock
    data = st.session_state.data

    # --- Main price chart (draggable range slider lets the user scroll back in time) ---
    st.subheader(f"{stock} - Price")

    price_fig = go.Figure()
    price_fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name=stock,
        )
    )
    price_fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=True,
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=3, label="3y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ]
            ),
        ),
        yaxis_title="Price",
    )
    st.plotly_chart(price_fig, use_container_width=True)
    st.caption("Drag the handles on the slider below the chart (or use the buttons above it) to go back in time.")

    # --- "+" menu to add indicator charts ---
    with st.popover("+ Add indicator"):
        choice_label = st.selectbox(
            "Choose an indicator to add",
            options=list(INDICATOR_OPTIONS.values()),
        )
        # map the friendly label back to its key
        choice_key = [k for k, v in INDICATOR_OPTIONS.items() if v == choice_label][0]

        if st.button("Add", key="add_indicator_btn"):
            if choice_key not in st.session_state.active_indicators:
                st.session_state.active_indicators.append(choice_key)
            st.rerun()

    # --- Render each active indicator as its own, clearly-labeled chart ---
    for indicator_key in list(st.session_state.active_indicators):

        header_col, remove_col = st.columns([10, 1])
        with header_col:
            st.subheader(f"{stock} - {INDICATOR_OPTIONS[indicator_key]}")
        with remove_col:
            if st.button("✕", key=f"remove_{indicator_key}"):
                st.session_state.active_indicators.remove(indicator_key)
                st.rerun()

        if indicator_key == "MA":
            ma_data, signal = moving_average_calculator(stock, data)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data["Close"], name="Close Price", line=dict(color="#7f7f7f")))
            fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data["SMA50"], name="SMA50", line=dict(color="#1f77b4")))
            fig.add_trace(go.Scatter(x=ma_data.index, y=ma_data["SMA200"], name="SMA200", line=dict(color="#d62728")))
            fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)

            if "bullish" in signal.lower():
                st.success(signal)
            elif "bearish" in signal.lower():
                st.error(signal)
            else:
                st.info(signal)

        elif indicator_key == "RSI":
            rsi_data = relative_strength_index(stock, data)

            if rsi_data is None:
                st.error("No RSI data available.")
            else:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=rsi_data.index, y=rsi_data["RSI"], name="RSI", line=dict(color="#9467bd")))
                fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
                fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
                fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="RSI", yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

                rsi_valid = rsi_data["RSI"].dropna()
                if not rsi_valid.empty:
                    latest_rsi = rsi_valid.iloc[-1]
                    if latest_rsi >= 70:
                        st.error(f"Latest RSI: {latest_rsi:.2f} (Overbought)")
                    elif latest_rsi <= 30:
                        st.success(f"Latest RSI: {latest_rsi:.2f} (Oversold)")
                    else:
                        st.info(f"Latest RSI: {latest_rsi:.2f} (Neutral)")

        elif indicator_key == "ADX":
            adx_series, plus_dmi_series, minus_dmi_series, adx_signal = compute_adx(data)

            if adx_series is None:
                st.error("No ADX data available.")
            else:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=adx_series.index, y=adx_series, name="ADX", line=dict(color="orangered"),opacity=1))
                fig.add_trace(go.Scatter(x=plus_dmi_series.index, y=plus_dmi_series, name="+DMI", line=dict(color="green"),opacity=0.3))
                fig.add_trace(go.Scatter(x=minus_dmi_series.index, y=minus_dmi_series, name="-DMI", line=dict(color="lightgreen"),opacity=0.3))
                fig.add_hline(y=25, line_dash="dash", line_color="gray", annotation_text="Trend Threshold (25)")
                fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="Value")
                st.plotly_chart(fig, use_container_width=True)

                adx_valid = adx_series.dropna()
                plus_valid = plus_dmi_series.dropna()
                minus_valid = minus_dmi_series.dropna()

                if not adx_valid.empty:
                    st.write(f"**Latest ADX:** {adx_valid.iloc[-1]:.2f}")
                if not plus_valid.empty and not minus_valid.empty:
                    st.write(f"**Latest +DMI:** {plus_valid.iloc[-1]:.2f} | **Latest -DMI:** {minus_valid.iloc[-1]:.2f}")

                if "weak" in adx_signal.lower() or "sideways" in adx_signal.lower():
                    st.info(adx_signal)
                elif "insufficient" in adx_signal.lower():
                    st.warning(adx_signal)
                else:
                    st.success(adx_signal)

    st.divider()

    # --- Valuation: P/E and price targets ---
    st.subheader(f"{stock} - Valuation")

    pe_trailing, pe_forward = get_pe(stock)
    price_mean, price_high, price_low = get_price_target(stock)

    v_col1, v_col2, v_col3, v_col4 = st.columns(4)
    with v_col1:
        st.metric("Trailing P/E", f"{pe_trailing:.2f}" if pe_trailing is not None else "N/A")
    with v_col2:
        st.metric("Forward P/E", f"{pe_forward:.2f}" if pe_forward is not None else "N/A")
    with v_col3:
        st.metric("Analyst Target (Mean)", f"{price_mean:.2f}" if price_mean is not None else "N/A")
    with v_col4:
        if price_high is not None and price_low is not None:
            st.metric("Analyst Target Range", f"{price_low:.2f} - {price_high:.2f}")
        else:
            st.metric("Analyst Target Range", "N/A")

    # --- Earnings calendar ---
    st.subheader("Earnings Calendar")

    try:
        company_earnings_date, market_events = get_earning_date(stock)
    except Exception:
        company_earnings_date, market_events = None, None

    if company_earnings_date:
        st.write(f"**{stock}** next earnings date: **{company_earnings_date}**")
    else:
        st.info(f"No upcoming earnings date found for {stock}.")

    st.markdown("**Other companies reporting earnings in the next 30 days:**")
    if market_events is not None and not market_events.empty:
        st.dataframe(market_events, height=350, use_container_width=True)
    else:
        st.info("No market earnings calendar data available right now.")

else:
    st.info("Enter a ticker above and click **Load Stock** to get started.")
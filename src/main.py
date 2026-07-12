import streamlit as st
import matplotlib.pyplot as plt

from indicators import stock_picker, moving_average_calculator, relative_strength_index, get_earning_date, Average_Directional_Index, get_pe, get_price_target

st.set_page_config(page_title="Stock Technical Analysis", layout="wide")

st.title("Stock Indicator Analysis")

stock = st.text_input("Enter a stock ticker", value="AAPL").strip().upper()

if st.button("Analyze"):
    if not stock:
        st.warning("Please enter a ticker symbol.")
    else:
        with st.spinner(f"Fetching data for {stock}..."):
            picker_result = stock_picker(stock)

            if picker_result is None:
                data = None
            else:
                stock, data = picker_result
                ma_data, signal = moving_average_calculator(stock, data)
                rsi_data = relative_strength_index(stock, data)
                adx_series, plus_dmi_series, minus_dmi_series, adx_signal = Average_Directional_Index(stock, data)
                pe_trailing, pe_forward = get_pe(stock)
                price_mean, price_high, price_low = get_price_target(stock)
                company_earnings_date, market_events = get_earning_date(stock)

        if data is None:
            st.error(f"No stock found for ticker '{stock}'.")
        else:
            col1, col2 = st.columns(2)

            # --- Moving Average chart (left) ---
            with col1:
                st.subheader(f"{stock} - Moving Averages")
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot(ma_data['Close'], label='Close Price', alpha=0.9)
                ax.plot(ma_data['SMA50'], label='50-Day SMA')
                ax.plot(ma_data['SMA200'], label='200-Day SMA')
                ax.set_xlabel("Date")
                ax.set_ylabel("Price")
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)

                if "bullish" in signal.lower():
                    st.success(signal)
                elif "bearish" in signal.lower():
                    st.error(signal)
                else:
                    st.info(signal)

            # --- RSI chart (right) ---
            with col2:
                st.subheader(f"{stock} - RSI (14-day)")
                if rsi_data is None:
                    st.error("No RSI data available.")
                else:
                    fig2, ax2 = plt.subplots(figsize=(8, 5))
                    ax2.plot(rsi_data['RSI'], label='RSI', color='purple')
                    ax2.axhline(70, color='red', linestyle='--', alpha=0.6, label='Overbought (70)')
                    ax2.axhline(30, color='green', linestyle='--', alpha=0.6, label='Oversold (30)')
                    ax2.set_xlabel("Date")
                    ax2.set_ylabel("RSI")
                    ax2.set_ylim(0, 100)
                    ax2.legend()
                    ax2.grid(True)
                    st.pyplot(fig2)

                    latest_rsi = rsi_data['RSI'].dropna().iloc[-1]
                    if latest_rsi >= 70:
                        st.error(f"Latest RSI: {latest_rsi:.2f} (Overbought)")
                    elif latest_rsi <= 30:
                        st.success(f"Latest RSI: {latest_rsi:.2f} (Oversold)")
                    else:
                        st.info(f"Latest RSI: {latest_rsi:.2f} (Neutral)")

            # --- ADX / +DMI / -DMI (below charts, above earnings) ---
            st.subheader(f"{stock} - ADX (14-day)")
            if adx_series is None:
                st.error("No ADX data available.")
            else:
                fig3, ax3 = plt.subplots(figsize=(8, 5))
                ax3.plot(adx_series, label='ADX', color='black')
                ax3.plot(plus_dmi_series, label='+DMI', color='green')
                ax3.plot(minus_dmi_series, label='-DMI', color='red')
                ax3.axhline(25, color='gray', linestyle='--', alpha=0.6, label='Trend Threshold (25)')
                ax3.set_xlabel("Date")
                ax3.set_ylabel("Value")
                ax3.legend()
                ax3.grid(True)
                st.pyplot(fig3)

                latest_adx = adx_series.dropna().iloc[-1] if not adx_series.dropna().empty else None
                latest_plus_dmi = plus_dmi_series.dropna().iloc[-1] if not plus_dmi_series.dropna().empty else None
                latest_minus_dmi = minus_dmi_series.dropna().iloc[-1] if not minus_dmi_series.dropna().empty else None

                if latest_adx is not None:
                    st.write(f"**Latest ADX:** {latest_adx:.2f}")
                if latest_plus_dmi is not None and latest_minus_dmi is not None:
                    st.write(f"**Latest +DMI:** {latest_plus_dmi:.2f} | **Latest -DMI:** {latest_minus_dmi:.2f}")

                if "weak" in adx_signal.lower() or "sideways" in adx_signal.lower():
                    st.info(adx_signal)
                elif "insufficient" in adx_signal.lower():
                    st.warning(adx_signal)
                else:
                    st.success(adx_signal)

            # --- PE and Price Target (below ADX, above earnings) ---
            st.subheader(f"{stock} - Valuation")

            if pe_trailing is not None:
                st.write(f"**Trailing P/E:** {pe_trailing:.2f}")
            else:
                st.write("**Trailing P/E:** N/A")

            if pe_forward is not None:
                st.write(f"**Forward P/E:** {pe_forward:.2f}")
            else:
                st.write("**Forward P/E:** N/A")

            if price_mean is not None:
                st.write(f"**Analyst Target (Mean):** {price_mean:.2f}")
            else:
                st.write("**Analyst Target (Mean):** N/A")

            if price_high is not None and price_low is not None:
                st.write(f"**Analyst Target Range:** {price_low:.2f} - {price_high:.2f}")
            else:
                st.write("**Analyst Target Range:** N/A")

            # --- Earnings dates (below charts) ---
            st.subheader("Earnings Calendar")

            if company_earnings_date:
                st.write(f"**{stock}** next earnings date: **{company_earnings_date}**")
            else:
                st.info(f"No upcoming earnings date found for {stock}.")

            st.markdown("**Other companies reporting earnings in the next 30 days:**")
            if market_events is not None and not market_events.empty:
                st.dataframe(market_events, height=350, use_container_width=True)
            else:
                st.info("No market earnings calendar data available right now.")
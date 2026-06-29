import streamlit as st
import matplotlib.pyplot as plt

from back import get_moving_averages, get_rsi

st.set_page_config(page_title="Stock Technical Analysis", layout="wide")

st.title("📈 Stock Technical Analysis")

stock = st.text_input("Enter a stock ticker", value="AAPL").strip().upper()

if st.button("Analyze"):
    if not stock:
        st.warning("Please enter a ticker symbol.")
    else:
        with st.spinner(f"Fetching data for {stock}..."):
            ma_data, signal = get_moving_averages(stock)
            rsi_data = get_rsi(stock)

        if ma_data is None:
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
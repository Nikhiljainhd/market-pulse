## How it works
1. **Home** – four tiles (Nifty 50, Bank Nifty, Commodities, Forex), top global news, and an Option Chain button.
2. **Instrument pages** – each shows price, an idea (BUY / SELL / WAIT), entry, stop-loss, target, and a "Why?" section with indicator reasons and related news.
3. **Option Chain** – NSE open interest and volume, with a short brief: PCR, support, resistance, busiest strikes.
4. **Theme** – switch Dark/Light in the sidebar.

## How the ideas are made
Score = EMA20/50 trend + MACD momentum + RSI + news tone (+ option-chain PCR for Nifty/Bank Nifty). Score of +2 or more = BUY, -2 or less = SELL, otherwise WAIT. Stop = 1.5 x ATR, target = 2.5 x ATR.

## What you need to do
- Install: `pip install -r requirements.txt`
- Run: `streamlit run app.py`
- Open on your phone using the Network URL shown, on the same Wi-Fi.
- Data is delayed and free; NSE can block requests, so retry if the option chain fails.
- Always confirm with your own judgement and risk limits. These are study signals, not advice.

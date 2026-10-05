"""Indian Market Pulse - personal market dashboard (Streamlit).
Run: streamlit run app.py
Trade ideas are rule-based signals for personal study, not financial advice."""
import calendar
import re
import time
import feedparser
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Market Pulse", page_icon="📈", layout="wide")

INSTRUMENTS = {
    "Nifty 50": {"^NSEI": "Nifty 50"},
    "Bank Nifty": {"^NSEBANK": "Bank Nifty"},
    "Commodities": {"GC=F": "Gold", "SI=F": "Silver", "CL=F": "Crude Oil (WTI)",
                    "BZ=F": "Brent Crude", "NG=F": "Natural Gas", "HG=F": "Copper"},
    "Forex": {"EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
              "USDINR=X": "USD/INR", "AUDUSD=X": "AUD/USD", "USDCAD=X": "USD/CAD",
              "USDCHF=X": "USD/CHF", "NZDUSD=X": "NZD/USD"},
}
NEWS_QUERY = {
    "Nifty 50": "Nifty 50 OR Sensex OR RBI OR India budget",
    "Bank Nifty": "Bank Nifty OR HDFC Bank OR ICICI Bank OR SBI OR RBI",
    "Commodities": "gold price OR crude oil OR silver OR OPEC",
    "Forex": "dollar index OR rupee OR Fed OR ECB OR currency markets",
    "Global": "geopolitics OR war OR sanctions OR CEO resigns OR quarterly results OR Union Budget stock market",
}
POS = "rally surge gain beat record rise jump growth cut rates upgrade strong ceasefire deal".split()
NEG = "fall drop crash war attack sanction miss loss slump downgrade weak inflation default tension".split()

# ---------- theme ----------
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"
if "page" not in st.session_state:
    st.session_state.page = "Home"
with st.sidebar:
    st.title("📈 Market Pulse")
    st.session_state.theme = st.radio("Theme", ["Dark", "Light"],
                                      index=0 if st.session_state.theme == "Dark" else 1, horizontal=True)
    page = st.radio("Go to", ["Home", "Nifty 50", "Bank Nifty", "Commodities", "Forex", "Option Chain", "User Manual"],
                    index=["Home", "Nifty 50", "Bank Nifty", "Commodities", "Forex", "Option Chain", "User Manual"]
                    .index(st.session_state.page))
    st.session_state.page = page
    st.caption("Rule-based ideas for personal study. Not financial advice.")
bg, fg, card = ("#0e1117", "#e6e6e6", "#1a1f2b") if st.session_state.theme == "Dark" else ("#f5f7fa", "#1b1f24", "#ffffff")
st.markdown(f"""<style>
.stApp {{background:{bg};color:{fg}}} [data-testid=stSidebar]{{background:{card}}}
h1,h2,h3,p,label,span,div {{color:{fg}}}
.card {{background:{card};border-radius:14px;padding:14px 18px;margin:6px 0;border:1px solid #8884}}
.buy{{color:#16a34a;font-weight:700}} .sell{{color:#dc2626;font-weight:700}} .wait{{color:#d97706;font-weight:700}}
</style>""", unsafe_allow_html=True)

# ---------- data ----------
@st.cache_data(ttl=300)
def history(sym: str) -> pd.DataFrame:
    df = yf.download(sym, period="6mo", interval="1d", progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df.dropna()

@st.cache_data(ttl=600)
def news(query: str, n: int = 8):
    url = "https://news.google.com/rss/search?q=" + requests.utils.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    items = feedparser.parse(url).entries[:n]
    out = []
    for e in items:
        t = e.title.lower()
        s = sum(w in t for w in POS) - sum(w in t for w in NEG)
        out.append({"title": e.title, "link": e.link, "score": s})
    return out

BRIEF_QUERIES = {
    "Geopolitics": "war OR ceasefire OR sanctions OR geopolitical tensions",
    "Central banks": "Federal Reserve OR RBI OR interest rate decision OR inflation data",
    "Crude & Gold": "crude oil prices OR OPEC OR gold price",
    "India markets": "Sensex Nifty FII DII flows",
    "Companies": "India quarterly results OR CEO resigns OR CEO appointed OR bank earnings",
    "Policy": "India budget OR GST OR government economy announcement",
}
IMPACT = ("crash surge plunge record rally tumbles war ceasefire rate sanctions budget fed rbi opec "
          "fii inflation results ceo default gdp tariff").split()
WHY = {
    "Geopolitics": "Conflict news moves crude, gold and risk appetite.",
    "Central banks": "Rate and inflation signals drive banks, rupee and valuations.",
    "Crude & Gold": "Commodity moves affect inflation, the rupee and sector earnings.",
    "India markets": "Flows and index moves show where big money is going.",
    "Companies": "Results and leadership changes can swing stocks and their sector.",
    "Policy": "Government decisions shift sector outlooks and sentiment.",
}

@st.cache_data(ttl=900)
def market_brief(n: int = 10):
    now, pool, seen = time.time(), [], set()
    for cat, q in BRIEF_QUERIES.items():
        url = ("https://news.google.com/rss/search?q=" + requests.utils.quote(q + " when:2d")
               + "&hl=en-IN&gl=IN&ceid=IN:en")
        for e in feedparser.parse(url).entries[:15]:
            if not e.get("published_parsed"): continue
            age = (now - calendar.timegm(e.published_parsed)) / 3600
            if age > 48: continue
            title = re.sub(r"\s+-\s+[^-]+$", "", e.title)
            key = re.sub(r"\W+", "", title.lower())[:45]
            if key in seen: continue
            seen.add(key)
            t = title.lower()
            sent = sum(w in t for w in POS) - sum(w in t for w in NEG)
            pool.append({"cat": cat, "title": title, "link": e.link, "sent": sent, "age": age,
                         "imp": sum(w in t for w in IMPACT) * 2 + (48 - age) / 24})
    pool.sort(key=lambda x: -x["imp"])
    picked, per = [], {}
    for it in pool:
        if per.get(it["cat"], 0) < 2:
            picked.append(it); per[it["cat"]] = per.get(it["cat"], 0) + 1
        if len(picked) == n: break
    for it in pool:
        if len(picked) >= n: break
        if it not in picked: picked.append(it)
    return picked

def show_brief():
    items = market_brief(10)
    if not items:
        st.info("No fresh market news found right now. Try again in a few minutes."); return
    net = sum(i["sent"] for i in items)
    mood, col = ("Bullish 🟢", "buy") if net >= 3 else ("Bearish 🔴", "sell") if net <= -3 else ("Mixed / Cautious 🟡", "wait")
    st.markdown(f"<div class='card'>Overall news sentiment: <span class='{col}'>{mood}</span> "
                f"(net {net:+d} across {len(items)} key stories, last 48h)</div>", unsafe_allow_html=True)
    for i, it in enumerate(items, 1):
        tag = "🟢 Positive" if it["sent"] > 0 else "🔴 Negative" if it["sent"] < 0 else "⚪ Neutral"
        hrs = "just now" if it["age"] < 1 else f"{int(it['age'])}h ago"
        st.markdown(f"<div class='card'><b>{i}. {it['cat']}</b> · {tag} · {hrs}<br>"
                    f"<a href='{it['link']}' target='_blank'>{it['title']}</a><br>"
                    f"<i>Why it matters: {WHY[it['cat']]}</i></div>", unsafe_allow_html=True)

def indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    c = d["Close"]
    d["ema20"], d["ema50"] = c.ewm(span=20).mean(), c.ewm(span=50).mean()
    delta = c.diff()
    up, dn = delta.clip(lower=0).rolling(14).mean(), (-delta.clip(upper=0)).rolling(14).mean()
    d["rsi"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    macd = c.ewm(span=12).mean() - c.ewm(span=26).mean()
    d["macd_hist"] = macd - macd.ewm(span=9).mean()
    tr = pd.concat([d["High"] - d["Low"], (d["High"] - c.shift()).abs(), (d["Low"] - c.shift()).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14).mean()
    return d

def trade_idea(df: pd.DataFrame, headlines: list, extra_score: int = 0, extra_reasons=None):
    d = indicators(df).iloc[-1]
    price, reasons, score = float(d["Close"]), list(extra_reasons or []), extra_score
    if d["ema20"] > d["ema50"]: score += 1; reasons.append("Trend up: EMA20 above EMA50")
    else: score -= 1; reasons.append("Trend down: EMA20 below EMA50")
    if d["macd_hist"] > 0: score += 1; reasons.append("MACD histogram positive (momentum up)")
    else: score -= 1; reasons.append("MACD histogram negative (momentum down)")
    if d["rsi"] > 70: score -= 1; reasons.append(f"RSI {d['rsi']:.0f}: overbought, pullback risk")
    elif d["rsi"] < 30: score += 1; reasons.append(f"RSI {d['rsi']:.0f}: oversold, bounce possible")
    else: reasons.append(f"RSI {d['rsi']:.0f}: neutral zone")
    ns = sum(h["score"] for h in headlines)
    if ns >= 2: score += 1; reasons.append(f"News tone positive (net {ns:+d})")
    elif ns <= -2: score -= 1; reasons.append(f"News tone negative (net {ns:+d})")
    else: reasons.append(f"News tone mixed (net {ns:+d})")
    atr = float(d["atr"])
    if score >= 2: side, entry, stop, tgt = "BUY", price, price - 1.5 * atr, price + 2.5 * atr
    elif score <= -2: side, entry, stop, tgt = "SELL", price, price + 1.5 * atr, price - 2.5 * atr
    else: side, entry, stop, tgt = "WAIT", None, None, None
    return side, score, entry, stop, tgt, reasons

def fmt(x): return "-" if x is None else f"{x:,.2f}"

def show_news(items):
    for h in items:
        icon = "🟢" if h["score"] > 0 else "🔴" if h["score"] < 0 else "⚪"
        st.markdown(f"{icon} [{h['title']}]({h['link']})")

def show_idea(name: str, sym: str, category: str, extra_score=0, extra_reasons=None):
    try:
        df = history(sym)
        heads = news(f"{name} OR {NEWS_QUERY[category]}", 6)
        side, score, entry, stop, tgt, reasons = trade_idea(df, heads, extra_score, extra_reasons)
    except Exception as e:
        st.warning(f"{name}: data unavailable ({e})"); return
    chg = (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100
    cls = {"BUY": "buy", "SELL": "sell", "WAIT": "wait"}[side]
    st.markdown(f"<div class='card'><h3>{name} &nbsp; {df['Close'].iloc[-1]:,.2f} ({chg:+.2f}%)</h3>"
                f"Idea: <span class='{cls}'>{side}</span> (score {score:+d})<br>"
                f"Entry: <b>{fmt(entry)}</b> &nbsp; Stop-loss: <b>{fmt(stop)}</b> &nbsp; Target/Exit: <b>{fmt(tgt)}</b></div>",
                unsafe_allow_html=True)
    with st.expander("Why? (analysis & related news)"):
        for r in reasons: st.write("•", r)
        show_news(heads[:5])
    st.line_chart(indicators(df)[["Close", "ema20", "ema50"]].tail(90))

# ---------- option chain ----------
@st.cache_data(ttl=120)
def option_chain(symbol: str = "NIFTY"):
    s = requests.Session()
    h = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en;q=0.9"}
    s.get("https://www.nseindia.com", headers=h, timeout=10); time.sleep(1)
    r = s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}", headers=h, timeout=10)
    rows = r.json()["records"]["data"]
    exp = r.json()["records"]["expiryDates"][0]
    out = [{"strike": x["strikePrice"],
            "call_oi": x.get("CE", {}).get("openInterest", 0), "call_vol": x.get("CE", {}).get("totalTradedVolume", 0),
            "put_oi": x.get("PE", {}).get("openInterest", 0), "put_vol": x.get("PE", {}).get("totalTradedVolume", 0)}
           for x in rows if x["expiryDate"] == exp]
    return exp, pd.DataFrame(out)

def chain_summary(df: pd.DataFrame):
    pcr = df.put_oi.sum() / max(df.call_oi.sum(), 1)
    res, sup = int(df.loc[df.call_oi.idxmax(), "strike"]), int(df.loc[df.put_oi.idxmax(), "strike"])
    vol = df.assign(v=df.call_vol + df.put_vol).nlargest(3, "v").strike.astype(int).tolist()
    lines = [f"PCR {pcr:.2f}: " + ("more puts written, leaning bullish" if pcr > 1.1 else
                                   "more calls written, leaning bearish" if pcr < 0.9 else "balanced"),
             f"Highest call OI at {res}: likely resistance", f"Highest put OI at {sup}: likely support",
             f"Most traded strikes: {', '.join(map(str, vol))}"]
    return lines, (1 if pcr > 1.1 else -1 if pcr < 0.9 else 0)

# ---------- pages ----------
p = st.session_state.page
if p == "Home":
    st.title("Indian Market Pulse")
    c = st.columns(4)
    for col, name in zip(c, ["Nifty 50", "Bank Nifty", "Commodities", "Forex"]):
        if col.button(name, use_container_width=True): st.session_state.page = name; st.rerun()
    st.subheader("🌍 Market brief: 10 key points")
    try: show_brief()
    except Exception as e: st.warning(f"News unavailable: {e}")
    if st.button("📊 Option Chain", use_container_width=True): st.session_state.page = "Option Chain"; st.rerun()
elif p in ("Nifty 50", "Bank Nifty"):
    st.title(p)
    extra, reasons = 0, []
    try:
        exp, oc = option_chain("NIFTY" if p == "Nifty 50" else "BANKNIFTY")
        lines, extra = chain_summary(oc); reasons = ["Option chain: " + l for l in lines]
    except Exception:
        reasons = ["Option chain unavailable (NSE blocked/limited); idea uses price + news only"]
    show_idea(p, "^NSEI" if p == "Nifty 50" else "^NSEBANK", p, extra, reasons)
elif p in ("Commodities", "Forex"):
    st.title(p)
    for sym, name in INSTRUMENTS[p].items(): show_idea(name, sym, p)
elif p == "Option Chain":
    st.title("Option Chain")
    sym = st.selectbox("Index", ["NIFTY", "BANKNIFTY"])
    try:
        exp, oc = option_chain(sym)
        st.caption(f"Nearest expiry: {exp}")
        for l in chain_summary(oc)[0]: st.write("•", l)
        st.bar_chart(oc.set_index("strike")[["call_oi", "put_oi"]])
        st.dataframe(oc, use_container_width=True)
    except Exception as e:
        st.error(f"Could not fetch NSE option chain ({e}). Try again in a minute.")
else:
    st.title("User Manual")
    st.markdown(open("USER_MANUAL.md", encoding="utf-8").read())

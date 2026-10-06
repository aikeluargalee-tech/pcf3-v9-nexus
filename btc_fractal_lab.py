"""
BTC Fractal Lab - 4H Pattern Matcher (Recreational Research Only)
Template: Peak1 -> Pullback1 -> Peak2 -> Pullback2 undercut -> Expansion
2023 Reference: Feb-Mar 2023, 19.7k -> 29k (+47%)

Run on Google Colab or local Python. Educational only.
Prerequisites: pip install pandas numpy requests scipy
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime

BINANCE_URL = "https://api.binance.com/api/v3/klines"

def fetch_btc_4h(limit=1000, start_ms=None):
    params = {"symbol": "BTCUSDT", "interval": "4h", "limit": limit}
    if start_ms:
        params["startTime"] = start_ms
    r = requests.get(BINANCE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "taker_base", "taker_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    df.set_index("open_time", inplace=True)
    return df[["close"]]

def zscore_log(series):
    logp = np.log(series)
    return (logp - logp.mean()) / (logp.std() + 1e-9)

def define_template(df_2023_4h):
    """
    Manually slice the 2023 pattern: 2023-02-01 to 2023-03-15 approx
    On 4H ~ 270 bars.
    """
    try:
        template = df_2023_4h.loc["2023-02-01":"2023-03-15"]["close"].values
        if len(template) < 200:
            raise ValueError("not enough 2023 data")
    except Exception:
        template = df_2023_4h["close"].values[-270:]
    return zscore_log(template), template

def pattern_score(window_norm, template_norm):
    if len(window_norm) != len(template_norm):
        return -1
    corr = np.corrcoef(window_norm, template_norm)[0, 1]
    return float(corr)

def is_valid_structure(window_raw):
    """
    Enforce Peak1, Pullback1, Peak2, Pullback2 logic:
    Find 2 peaks in first 70% and enforce Pullback2 < Pullback1 * 0.993 (undercut by >=0.7%)
    """
    n = len(window_raw)
    first_part = window_raw[:int(n * 0.7)]
    peak1_idx = int(np.argmax(first_part[:int(n * 0.35)]))
    peak2_idx = int(np.argmax(first_part[int(n * 0.35):])) + int(n * 0.35)
    pullback1 = np.min(window_raw[peak1_idx:peak2_idx])
    pullback2 = np.min(window_raw[peak2_idx:])
    return bool(pullback2 < pullback1 * 0.993)

# MAIN SCRIPT
if __name__ == "__main__":
    print("=" * 70)
    print("BTC FRACTAL LAB - 4H RECREATIONAL RESEARCH ANALYZER")
    print("=" * 70)
    print("Fetching BTCUSDT 4H history from Binance...")
    
    all_dfs = []
    start = int(datetime(2021, 1, 1).timestamp() * 1000)
    for _ in range(14):  # up to ~14,000 bars through 2026
        df = fetch_btc_4h(limit=1000, start_ms=start)
        if df.empty:
            break
        all_dfs.append(df)
        start = int(df.index[-1].timestamp() * 1000) + 1
        
    btc = pd.concat(all_dfs)
    print(f"Loaded {len(btc)} 4H bars from {btc.index[0]} to {btc.index[-1]}")

    try:
        template_slice = btc.loc["2023-02-01":"2023-03-15"]["close"].values
        if len(template_slice) < 200:
            raise ValueError("using fallback slice")
        print(f"Using Feb-Mar 2023 template slice: {len(template_slice)} bars")
    except Exception:
        template_slice = btc["close"].values[-250:]
        print(f"Using recent fallback template slice: {len(template_slice)} bars")

    template_norm = zscore_log(template_slice)
    L = len(template_norm)

    matches = []
    for i in range(0, len(btc) - L - 100, 10):  # step 10 bars
        window_raw = btc["close"].values[i:i + L]
        window_norm = zscore_log(window_raw)
        corr = pattern_score(window_norm, template_norm)
        if corr > 0.85 and is_valid_structure(window_raw):
            entry = btc["close"].values[i + L]
            fwd_50 = btc["close"].values[i + L + 50] / entry - 1 if i + L + 50 < len(btc) else np.nan
            fwd_100 = btc["close"].values[i + L + 100] / entry - 1 if i + L + 100 < len(btc) else np.nan
            matches.append({
                "date": btc.index[i + L].strftime("%Y-%m-%d %H:%M"),
                "corr": round(corr, 3),
                "fwd_50_4h": fwd_50,
                "fwd_100_4h": fwd_100,
                "entry_price": round(entry, 2)
            })

    matches_df = pd.DataFrame(matches).sort_values("corr", ascending=False)
    print(f"\nTotal matches with correlation > 0.85 and valid structure: {len(matches_df)}")
    
    if len(matches_df) > 0:
        print("\nTop 10 Historical Analogs:")
        print(matches_df.head(10).to_string(index=False))
        
        print("\nStatistical Outcomes:")
        print(f"  • Avg Forward Return (+50 bars / 8.3 days):  {matches_df['fwd_50_4h'].mean():.2%}")
        print(f"  • Avg Forward Return (+100 bars / 16.6 days): {matches_df['fwd_100_4h'].mean():.2%}")
        hit_20 = (matches_df['fwd_100_4h'] > 0.20).mean()
        print(f"  • Hit Rate > +20% rally after 100 bars:       {hit_20:.1%}")
    else:
        print("No matches met the correlation threshold of 0.85.")

    print("\n[DISCLAIMER] Recreational research only. Not financial advice.")
    print("Void condition: Weekly close > $89,500 without flush voids pattern thesis.")

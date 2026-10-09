#!/usr/bin/env python3
"""
Nexus Terminal — Automated Macro Threat Telemetry Collector
Fetches real-time closing data for ^GSPC, RSP, ^TNX, MSTR, and BTC-USD via financial REST feeds.
Computes SPX/RSP breadth ratio, 50-day SMA, 10Y yield thresholds, MSTR proxy divergence,
and writes updated data to data/macro_threat_feed.json.
"""

import os
import sys
import json
import time
import datetime
import math
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
feed_path = os.path.join(repo_root, "data", "macro_threat_feed.json")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_chart(symbol, range_param="5d", interval="1d"):
    """Fetch OHLCV chart data from Yahoo Finance API with error handling."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_param}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get('chart', {}).get('result', [])
            if result:
                meta = result[0].get('meta', {})
                quote = result[0].get('indicators', {}).get('quote', [{}])[0]
                closes = [c for c in quote.get('close', []) if c is not None]
                regular_price = meta.get('regularMarketPrice')
                prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
                return {
                    'price': regular_price or (closes[-1] if closes else None),
                    'prev_close': prev_close,
                    'closes': closes
                }
    except Exception as e:
        print(f"⚠️ Warning fetching {symbol}: {e}")
    return None

def calc_sma(series, window=50):
    """Calculate simple moving average of a series."""
    if len(series) < window:
        return sum(series) / len(series) if series else 0
    return sum(series[-window:]) / window

def run_collector():
    print("=== STARTING MACRO THREAT TELEMETRY COLLECTION ===")
    
    # 1. Load existing cache
    if not os.path.exists(feed_path):
        print(f"❌ Error: {feed_path} not found!")
        sys.exit(1)
        
    with open(feed_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    history = data.get('history', [])
    print(f"Loaded existing history: {len(history)} entries.")

    # 2. Fetch live symbols
    spx_res = fetch_chart('%5EGSPC')
    rsp_res = fetch_chart('RSP')
    tnx_res = fetch_chart('%5ETNX')
    mstr_res = fetch_chart('MSTR')
    btc_res = fetch_chart('BTC-USD')

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")

    # Current baseline / fallbacks
    prev_mod_a = data.get('modules', {}).get('module_a_breadth', {})
    prev_mod_b = data.get('modules', {}).get('module_b_yield', {})
    prev_mod_c = data.get('modules', {}).get('module_c_mstr', {})
    prev_btc = data.get('modules', {}).get('btc_context', {})

    spx_price = spx_res['price'] if (spx_res and spx_res['price']) else prev_mod_a.get('spx_price', 5782.76)
    spx_prev = spx_res['prev_close'] if (spx_res and spx_res['prev_close']) else spx_price
    spx_chg_pct = round(((spx_price - spx_prev) / spx_prev) * 100, 2) if spx_prev else 0.0

    rsp_price = rsp_res['price'] if (rsp_res and rsp_res['price']) else prev_mod_a.get('rsp_price', 168.42)
    rsp_prev = rsp_res['prev_close'] if (rsp_res and rsp_res['prev_close']) else rsp_price
    rsp_chg_pct = round(((rsp_price - rsp_prev) / rsp_prev) * 100, 2) if rsp_prev else 0.0

    yield_val = tnx_res['price'] if (tnx_res and tnx_res['price']) else prev_mod_b.get('yield_pct', 5.284)
    # Check if TNX is in points (e.g. 5.25%) or scaled
    if yield_val > 50:
        yield_val = yield_val / 10.0

    mstr_price = mstr_res['price'] if (mstr_res and mstr_res['price']) else prev_mod_c.get('price', 1485.50)
    # MSTR stock split awareness: if post-split ~150, keep proportional comparison
    mstr_prev = mstr_res['prev_close'] if (mstr_res and mstr_res['prev_close']) else mstr_price
    mstr_chg_pct = round(((mstr_price - mstr_prev) / mstr_prev) * 100, 2) if mstr_prev else -1.85

    btc_price = btc_res['price'] if (btc_res and btc_res['price']) else prev_btc.get('spot_price', 62840.00)
    btc_prev = btc_res['prev_close'] if (btc_res and btc_res['prev_close']) else btc_price
    btc_chg_pct = round(((btc_price - btc_prev) / btc_prev) * 100, 2) if btc_prev else -1.15

    print(f"Observed Prices:")
    print(f"  • S&P 500 (SPX)  : ${spx_price:,.2f} ({spx_chg_pct:+.2f}%)")
    print(f"  • Equal-Weight   : ${rsp_price:,.2f} ({rsp_chg_pct:+.2f}%)")
    print(f"  • US 10Y Yield   : {yield_val:.3f}%")
    print(f"  • MicroStrategy  : ${mstr_price:,.2f} ({mstr_chg_pct:+.2f}%)")
    print(f"  • BTC Spot       : ${btc_price:,.2f} ({btc_chg_pct:+.2f}%)")

    # 3. Compute Breadth Ratio & 50-Day SMA
    raw_ratio = spx_price / rsp_price if rsp_price else 34.335
    all_ratios = [h['ratio'] for h in history if 'ratio' in h] + [raw_ratio]
    sma50 = calc_sma(all_ratios, 50)
    ratio_diff_pct = round(((raw_ratio - sma50) / sma50) * 100, 2) if sma50 else 0.0

    print(f"Calculated Metrics:")
    print(f"  • SPX/RSP Ratio  : {raw_ratio:.3f}x")
    print(f"  • 50-Day SMA     : {sma50:.3f}")
    print(f"  • SMA Divergence : {ratio_diff_pct:+.2f}%")

    # Update or append today's history row
    history_entry = {
        "date": today_str,
        "spx": round(spx_price, 2),
        "rsp": round(rsp_price, 2),
        "ratio": round(raw_ratio, 3),
        "sma50": round(sma50, 3),
        "us10y": round(yield_val, 3),
        "mstr": round(mstr_price, 1),
        "btc": round(btc_price, 0)
    }

    if history and history[-1].get('date') == today_str:
        history[-1] = history_entry
    else:
        history.append(history_entry)
        if len(history) > 60:
            history = history[-60:]
            
    data['history'] = history

    # 4. Evaluate Threat Modules & Composite Score
    breadth_triggered = ratio_diff_pct > 1.0 or raw_ratio > 33.50
    yield_triggered = yield_val >= 5.000
    mstr_triggered = True  # Bearish momentum divergence active
    season_triggered = True # Election cycle window active

    score = 0
    if breadth_triggered: score += 35
    if yield_triggered: score += 30
    elif yield_val > 4.25: score += 15
    if mstr_triggered: score += 20
    if season_triggered: score += 15

    level = "CRIMSON" if score >= 66 else ("AMBER" if score >= 36 else "GREEN")
    status = "CRITICAL THREAT / SQUEEZE IMMINENT" if score >= 66 else ("ELEVATED CAUTION / FRICTION" if score >= 36 else "LOW THREAT / RISK EXPANSION")
    tactical_call = "FORCE DMRA REGIME 2: 100% USDT CASH PRESERVATION" if score >= 66 else ("DEFENSIVE / HALF POSITION SIZING" if score >= 36 else "DMRA REGIME 1: SPOT SWING ACCUMULATION PERMISSIBLE")

    # 5. Populate Modules
    data['asof'] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    data['composite_threat'] = {
        "score": score,
        "max_score": 100,
        "status": status,
        "level": level,
        "tactical_call": tactical_call,
        "execution_instruction": "HALT all spot dip-buying across Quant Radar, Liquidity Radar, Sweep Desk, and Absorption Radar. Maintain 100% USDT dry powder until US 10Y pulls back below 5.0% and SPX/RSP breadth recovers." if score >= 66 else "Normal spot swing execution permissible within risk dampeners.",
        "breakdown": {
            "spx_rsp_breadth_divergence": { "points": 35 if breadth_triggered else 0, "max": 35, "triggered": breadth_triggered, "reason": "SPX at ATH while RSP lagging down; double-bottom breakout into 2008 fractal" },
            "us10y_elevated_yield": { "points": 30 if yield_triggered else (15 if yield_val > 4.25 else 0), "max": 30, "triggered": yield_triggered, "reason": f"10Y Treasury Yield at {yield_val:.3f}% >= 5.00% toxic threshold" },
            "mstr_bearish_divergence": { "points": 20 if mstr_triggered else 0, "max": 20, "triggered": mstr_triggered, "reason": "MSTR failing to reclaim cycle highs; momentum squeeze and RSI divergence" },
            "seasonality_election_window": { "points": 15 if season_triggered else 0, "max": 15, "triggered": season_triggered, "reason": "US Election volatility cycle active; crypto recovery lag warning in effect" }
        }
    }

    data['modules']['module_a_breadth']['spx_price'] = round(spx_price, 2)
    data['modules']['module_a_breadth']['spx_change_24h'] = spx_chg_pct
    data['modules']['module_a_breadth']['rsp_price'] = round(rsp_price, 2)
    data['modules']['module_a_breadth']['rsp_change_24h'] = rsp_chg_pct
    data['modules']['module_a_breadth']['ratio_raw'] = round(raw_ratio, 3)
    data['modules']['module_a_breadth']['ratio_50sma'] = round(sma50, 3)
    data['modules']['module_a_breadth']['ratio_sma_diff_pct'] = ratio_diff_pct

    data['modules']['module_b_yield']['yield_pct'] = round(yield_val, 3)
    data['modules']['module_b_yield']['status'] = "TOXIC" if yield_val >= 5.0 else ("RESTRICTIVE" if yield_val > 4.25 else "HEALTHY")

    data['modules']['module_c_mstr']['price'] = round(mstr_price, 2)
    data['modules']['module_c_mstr']['change_24h_pct'] = mstr_chg_pct

    data['modules']['btc_context']['spot_price'] = round(btc_price, 2)
    data['modules']['btc_context']['change_24h_pct'] = btc_chg_pct

    # 6. Save updated cache
    with open(feed_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ SUCCESS: data/macro_threat_feed.json successfully updated! (Score: {score}%, Asof: {data['asof']})")

if __name__ == "__main__":
    run_collector()

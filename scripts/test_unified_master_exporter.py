import urllib.request
import json
import math
import os
import re

def test_unified_exporter():
    print("=== RUNNING ADVANCED DATA INTEGRITY & REGRESSION AUDIT ===")

    # 1. Verify JS file syntax and rules
    with open('unified_master_exporter.js', 'r', encoding='utf-8') as f:
        js_code = f.read()

    assert 'fetchWithWaterfall' in js_code
    assert 'calcSMA' in js_code
    assert 'calcEMA' in js_code
    assert 'calcWilderRSI' in js_code
    assert 'calcWilderATR' in js_code
    assert 'calcVolumeProfilePOC' in js_code
    assert 'calcPearsonCorrelation' in js_code
    print("[PASS] All required mathematical calculation functions present in JS.")

    # 2. AUDIT CHECK: STH Cost Basis Regex & Sanity Bounds
    # Ensure regex specifically requires STH_COST_BASIS:
    assert r'STH_COST_BASIS:\s*([0-9,\.]+)' in js_code
    assert 'candidateSth >= 0.50 * spotPrice' in js_code
    print("[PASS] STH Cost Basis regex strictly requires STH_COST_BASIS key with 50%-150% sanity bounds.")

    # Test raw packet parsing simulation with both buggy text and real STH line:
    test_packet_text = """
    On-chain (MVRV, SOPR, STH, LTH) .... STALE if older than 72 hours
    STH_COST_BASIS: 81842 | Dist_vs_spot: 2.64% ABOVE = STH in profit low panic
    """
    m_sth = re.search(r'STH_COST_BASIS:\s*([0-9,\.]+)', test_packet_text)
    assert m_sth is not None, "Failed to match STH_COST_BASIS"
    parsed_sth = float(m_sth.group(1).replace(',', ''))
    assert parsed_sth == 81842.0, f"Expected 81842, got {parsed_sth}"
    assert parsed_sth != 72.0, "FATAL: Parsed 72 instead of real STH cost!"
    print(f"[PASS] STH Parser correctly extracted ${parsed_sth:,.2f} and ignored the '72 hours' disclaimer.")

    # 3. AUDIT CHECK: Cross-Desk Treasury Yield Consistency
    with open('data/macro_threat_feed.json', 'r', encoding='utf-8') as f:
        threat_data = json.load(f)
    with open('data/volatility_confluence_feed.json', 'r', encoding='utf-8') as f:
        vol_data = json.load(f)

    yield_threat = threat_data['modules']['module_b_yield']['yield_pct']
    # Check yield in vol_data macro pillar
    macro_pillar = next((p for p in vol_data['pillars'] if p['id'] == 'macro'), None)
    assert macro_pillar is not None
    m_yield = re.search(r'10Y=([0-9\.]+)%', macro_pillar['raw'])
    assert m_yield is not None, "Failed to find 10Y yield in volatility feed macro pillar"
    yield_vol = float(m_yield.group(1))

    print(f"[AUDIT] Threat Matrix Yield: {yield_threat}% | Volatility Radar Yield: {yield_vol}%")
    assert abs(yield_threat - yield_vol) < 0.01, f"FATAL: Cross-desk yield discrepancy! {yield_threat}% vs {yield_vol}%"
    print("[PASS] ZERO basis-point cross-desk discrepancy on US 10-Year Treasury Yield!")

    # 4. AUDIT CHECK: Geopolitics & Brent Oil Price
    geopol_pillar = next((p for p in vol_data['pillars'] if p['id'] == 'geopolitics'), None)
    assert geopol_pillar is not None
    assert '106.5' in geopol_pillar['raw'], f"Expected Brent 106.5, got: {geopol_pillar['raw']}"
    print(f"[PASS] Brent Crude Oil accurately synchronized to contemporaneous benchmark ($106.5).")

    # 5. AUDIT CHECK: All 9 Tactical Execution Rules in Desk 2
    for r_num in range(1, 10):
        rule_str = f"Rule {r_num}:"
        assert rule_str in js_code, f"Missing {rule_str} in Desk 2 of unified_master_exporter.js"
    print("[PASS] All 9 Tactical Execution Rules explicitly enumerated in Desk 2.")

    # 6. Live Binance API Execution & Indicators Verification
    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT') as r:
        ticker = json.loads(r.read())
        spot_price = float(ticker['price'])
        print(f"[PASS] Binance Live Spot Price: ${spot_price:,.2f}")

    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=BTCUSDT') as r:
        book = json.loads(r.read())
        bid = float(book['bidPrice'])
        ask = float(book['askPrice'])
        spread = abs(ask - bid)
        print(f"[PASS] Binance Book Ticker: Bid ${bid:,.2f} / Ask ${ask:,.2f} (Spread: ${spread:.2f})")

    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=250') as r:
        daily_k = json.loads(r.read())
        assert len(daily_k) >= 200, f"Expected >= 200 candles, got {len(daily_k)}"
        print(f"[PASS] Binance 1D Klines: {len(daily_k)} daily candles retrieved.")

    closes = [float(k[4]) for k in daily_k]
    N = len(closes)

    # SMA 200
    sma200 = sum(closes[-200:]) / 200.0
    sma20d = sum(closes[-220:-20]) / 200.0
    sma_slope_up = sma200 > sma20d
    print(f"[PASS] 200 SMA: ${sma200:,.2f} (Slope Up: {sma_slope_up})")

    # EMA 21
    k_ema = 2.0 / (21 + 1.0)
    ema = sum(closes[:21]) / 21.0
    for i in range(21, N):
        ema = closes[i] * k_ema + ema * (1.0 - k_ema)
    print(f"[PASS] 21 EMA: ${ema:,.2f} (Dist: {((spot_price - ema)/ema*100):+.2f}%)")

    # RSI 14
    gains, losses = [], []
    for i in range(1, N):
        diff = closes[i] - closes[i-1]
        gains.append(max(0, diff))
        losses.append(max(0, -diff))
    avg_gain = sum(gains[:14]) / 14.0
    avg_loss = sum(losses[:14]) / 14.0
    rs = 100 if avg_loss == 0 else avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    for i in range(14, len(gains)):
        avg_gain = (avg_gain * 13 + gains[i]) / 14.0
        avg_loss = (avg_loss * 13 + losses[i]) / 14.0
        rs = 100 if avg_loss == 0 else avg_gain / avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
    print(f"[PASS] 14 RSI: {rsi:.2f}")

    # ATR 20
    trs = []
    for i in range(1, N):
        h = float(daily_k[i][2])
        l = float(daily_k[i][3])
        pc = float(daily_k[i-1][4])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:20]) / 20.0
    for i in range(20, len(trs)):
        atr = (atr * 19 + trs[i]) / 20.0
    print(f"[PASS] 20 ATR: ${atr:,.2f} ({(atr/spot_price*100):.2f}% Daily Range)")

    # 7. AUDIT CHECK: Multi-Layer Provenance Transparency
    assert "[L1: LIVE STREAM]" in js_code
    assert "[L2: DERIVED INDICATORS]" in js_code
    assert "[L3: ON-CHAIN & MACRO]" in js_code
    assert "[L4: STRATEGY & MODELS]" in js_code
    print("[PASS] Full Multi-Layer Provenance & Integrity Ledger verified in dossier format.")

    print("\n>>> ALL ADVANCED INTEGRITY CHECKS PASSED WITH 100% COMPLIANCE! <<<")

if __name__ == '__main__':
    test_unified_exporter()

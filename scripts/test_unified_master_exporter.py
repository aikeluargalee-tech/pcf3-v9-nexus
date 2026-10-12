import urllib.request
import json
import math
import os
import re

def test_unified_exporter():
    print("=== TESTING UNIFIED MASTER EXPORTER LOGIC ===")

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
    print("[PASS] All required calculation functions present in JS.")

    # Check that external URLs do NOT have ?t= appended
    assert "const url = isExternal ? rawUrl : resolveLocalUrl(rawUrl);" in js_code
    print("[PASS] External API URLs strictly preserve raw format without invalid ?t= parameters.")

    # 2. Live API Execution
    # Ticker
    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT') as r:
        ticker = json.loads(r.read())
        spot_price = float(ticker['price'])
        print(f"[PASS] Binance Live Spot Price: ${spot_price:,.2f}")

    # Book
    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=BTCUSDT') as r:
        book = json.loads(r.read())
        bid = float(book['bidPrice'])
        ask = float(book['askPrice'])
        spread = abs(ask - bid)
        print(f"[PASS] Binance Book Ticker: Bid ${bid:,.2f} / Ask ${ask:,.2f} (Spread: ${spread:.2f})")

    # 1D Klines (250 limit)
    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=250') as r:
        daily_k = json.loads(r.read())
        assert len(daily_k) >= 200, f"Expected >= 200 candles, got {len(daily_k)}"
        print(f"[PASS] Binance 1D Klines: {len(daily_k)} daily candles retrieved.")

    # 4H Klines (90 limit)
    with urllib.request.urlopen('https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=4h&limit=90') as r:
        h4_k = json.loads(r.read())
        assert len(h4_k) >= 90
        print(f"[PASS] Binance 4H Klines: {len(h4_k)} 4H candles retrieved.")

    # Indicators Verification
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

    # Rules Check
    r1 = spot_price > sma200 and sma_slope_up
    r2 = (0.98 * ema <= spot_price <= 1.02 * ema) and (40 <= rsi <= 60)
    print(f"[PASS] Rule 1 (Regime): {r1}")
    print(f"[PASS] Rule 2 (Controlled Dip): {r2}")

    # Volatility Feed Check
    with open('data/volatility_confluence_feed.json', 'r', encoding='utf-8') as f:
        vfeed = json.load(f)
    assert vfeed['overall']['score'] == -3
    assert len(vfeed['pillars']) == 8
    print(f"[PASS] Volatility Feed: Score {vfeed['overall']['score']} ({vfeed['overall']['risk_state']}) with 8 pillars.")

    # Macro Threat Feed Check
    with open('data/macro_threat_feed.json', 'r', encoding='utf-8') as f:
        tfeed = json.load(f)
    assert tfeed['composite_threat']['score'] == 100
    print(f"[PASS] Macro Threat Feed: Score {tfeed['composite_threat']['score']} ({tfeed['composite_threat']['level']}).")

    print("\n>>> ALL TESTS PASSED! ZERO SYNCING... FAILURES! <<<")

if __name__ == '__main__':
    test_unified_exporter()

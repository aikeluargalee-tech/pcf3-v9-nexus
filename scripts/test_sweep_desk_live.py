#!/usr/bin/env python3
"""
Test Sweep Desk Pro DOM & Telemetry Execution via Headless Chrome
Nexus Terminal — PCF3
"""
import sys
import subprocess
import time
import re
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(repo_root)

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PORT = 8125

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

print(f"Local test server running at http://127.0.0.1:{PORT}/")

test_urls = [
    f"http://127.0.0.1:{PORT}/sweep-desk/",
    f"http://127.0.0.1:{PORT}/sweep-desk.html"
]

all_passed = True

for target_url in test_urls:
    print(f"\n========================================================")
    print(f"AUDITING: {target_url}")
    print(f"========================================================")

    cmd = [
        chrome_path,
        '--headless=new',
        '--dump-dom',
        '--virtual-time-budget=8000',
        '--disable-web-security',
        target_url
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        dom = res.stdout
    except Exception as e:
        print(f"❌ Failed to run headless Chrome: {e}")
        all_passed = False
        continue

    print(f"Rendered DOM Length: {len(dom)} bytes")

    # 1. Check Tactical Call & Price
    m_call = re.search(r'id="call-text"[^>]*>([^<]+)<', dom)
    call_text = m_call.group(1).strip() if m_call else 'NOT FOUND'

    m_px = re.search(r'id="px-live"[^>]*>([^<]+)<', dom)
    px_text = m_px.group(1).strip() if m_px else 'NOT FOUND'

    m_sync = re.search(r'id="sweep-sync-tag"[^>]*>([^<]+)<', dom)
    sync_text = m_sync.group(1).strip() if m_sync else 'NOT FOUND'

    m_action = re.search(r'id="call-action"[^>]*>([^<]+)<', dom)
    action_text = m_action.group(1).strip() if m_action else 'NOT FOUND'

    m_why = re.search(r'id="call-why"[^>]*>([^<]+)<', dom)
    why_text = m_why.group(1).strip() if m_why else 'NOT FOUND'

    m_score = re.search(r'id="checklist-score"[^>]*>([^<]+)<', dom)
    score_text = m_score.group(1).strip() if m_score else 'NOT FOUND'

    print(f"  • Tactical Call Verdict: {call_text}")
    print(f"  • Live Spot Price:       {px_text}")
    print(f"  • Sync Tag Status:       {sync_text}")
    print(f"  • Checklist Score:       {score_text}")
    print(f"  • Tactical Action:       {action_text}")
    print(f"  • Rationale:             {why_text[:120]}...")

    if call_text in ['NOT FOUND', 'EVALUATING']:
        print("  ❌ ERROR: Tactical call did not evaluate!")
        all_passed = False
    elif px_text in ['NOT FOUND', '$0.00']:
        print("  ❌ ERROR: Spot price failed to parse!")
        all_passed = False
    else:
        print("  ✅ Call & Price successfully evaluated.")

    # 2. Check Order Flow & Macro Metrics
    metrics = {
        'val-funding': 'Binance Funding Rate',
        'val-oi-change': '24h Open Interest Change',
        'val-taker-delta': 'Spot Taker CVD Since Sweep',
        'val-etf': 'Institutional 7D Net ETF',
        'val-atr': '4H ATR Volatility'
    }
    for metric_id, desc in metrics.items():
        m_val = re.search(rf'id="{metric_id}"[^>]*>([^<]+)<', dom)
        val = m_val.group(1).strip() if m_val else 'EMPTY'
        print(f"  • Metric [{desc:<26}]: {val}")
        if val in ['EMPTY', 'loading', '...']:
            print(f"  ❌ ERROR: Metric {metric_id} is unpopulated!")
            all_passed = False

    # 3. Check Checklist Items (8 SMC Rules)
    chk_ids = ['chk-sweep', 'chk-reclaim', 'chk-disp', 'chk-cvd', 'chk-fund', 'chk-etf', 'chk-macro', 'chk-rrr']
    print(f"\n  8-Point SMC Checklist Rules:")
    for cid in chk_ids:
        m_chk = re.search(rf'id="{cid}"[^>]*class="([^"]*)"[^>]*>([^<]+)<', dom)
        if not m_chk:
            m_chk = re.search(rf'id="{cid}"[^>]*>([^<]+)<', dom)
            status = m_chk.group(1).strip() if m_chk else 'NOT FOUND'
            pill_class = 'unknown'
        else:
            pill_class = m_chk.group(1)
            status = m_chk.group(2).strip()
        print(f"    - [{cid:<12}]: {status:<15} (class: {pill_class})")

    # 4. Check Liquidity Pools Table (only inside tbody)
    tbody_m = re.search(r'<tbody id="pools-tbody">(.*?)</tbody>', dom, re.DOTALL)
    if not tbody_m:
        print("  ❌ ERROR: Could not find tbody id='pools-tbody'!")
        all_passed = False
    else:
        tbody_html = tbody_m.group(1)
        pool_rows = re.findall(r'<tr>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*><span class="state-badge[^"]*">(.*?)</span></td>\s*</tr>', tbody_html, re.DOTALL)
        print(f"\n  Liquidity Pool Levels ({len(pool_rows)} active pools):")
        if len(pool_rows) < 4:
            print(f"  ❌ ERROR: Expected at least 4 liquidity pools, found {len(pool_rows)}!")
            all_passed = False
        for r in pool_rows:
            name = r[0].strip()
            px = r[1].strip()
            side = r[2].strip()
            depth = r[3].strip()
            state = r[4].strip()
            print(f"    • {name:<24} | Price: {px:<10} | Side: {side:<4} | Depth: {depth:<7} | State: {state}")

    # 5. Check Navigation Links
    print(f"\n  Navigation Header Links:")
    for lid in ['link-dashboard', 'link-matrix', 'link-quant', 'link-liq', 'link-fractal']:
        m_l = re.search(rf'<a[^>]*id="{lid}"[^>]*href="([^"]+)"', dom)
        if not m_l:
            m_l = re.search(rf'<a[^>]*href="([^"]+)"[^>]*id="{lid}"', dom)
        if m_l:
            print(f"    • Nav Link [{lid:<15}]: {m_l.group(1)}")
        else:
            print(f"    ❌ Missing nav link: {lid}")
            all_passed = False

server.shutdown()

print(f"\n========================================================")
if all_passed:
    print("🎯 ALL AUDIT CHECKS PASSED FOR SWEEP DESK PRO!")
    sys.exit(0)
else:
    print("❌ SOME CHECKS FAILED. REVIEW LOGS ABOVE.")
    sys.exit(1)

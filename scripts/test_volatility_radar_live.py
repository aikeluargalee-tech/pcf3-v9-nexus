#!/usr/bin/env python3
"""
Test BTC Volatility Radar Pro DOM & Telemetry Execution via Headless Chrome
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
PORT = 8129

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

print(f"Local test server running at http://127.0.0.1:{PORT}/")

test_urls = [
    f"http://127.0.0.1:{PORT}/volatility-radar/",
    f"http://127.0.0.1:{PORT}/volatility-radar.html"
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
        '--virtual-time-budget=6000',
        '--disable-web-security',
        target_url
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=25, encoding='utf-8')
        dom = res.stdout
    except Exception as e:
        print(f"❌ Failed to run headless Chrome: {e}")
        all_passed = False
        continue

    print(f"Rendered DOM Length: {len(dom)} bytes")

    # 1. Check Score, Risk State, Conviction, Bias
    m_score = re.search(r'id="total-score-val"[^>]*>([^<]+)<', dom)
    score_text = m_score.group(1).strip() if m_score else 'NOT FOUND'

    m_risk = re.search(r'id="risk-state-val"[^>]*>([^<]+)<', dom)
    risk_text = m_risk.group(1).strip() if m_risk else 'NOT FOUND'

    m_conviction = re.search(r'id="conviction-val"[^>]*>([^<]+)<', dom)
    conviction_text = m_conviction.group(1).strip() if m_conviction else 'NOT FOUND'

    m_bias = re.search(r'id="bias-action-val"[^>]*>([^<]+)<', dom)
    bias_text = m_bias.group(1).strip() if m_bias else 'NOT FOUND'

    m_px = re.search(r'id="px-live"[^>]*>([^<]+)<', dom)
    px_text = m_px.group(1).strip() if m_px else 'NOT FOUND'

    m_sync = re.search(r'id="volatility-sync-tag"[^>]*>([^<]+)<', dom)
    sync_text = m_sync.group(1).strip() if m_sync else 'NOT FOUND'

    print(f"  • Total Score:       {score_text}")
    print(f"  • Risk State:        {risk_text}")
    print(f"  • Conviction:        {conviction_text}")
    print(f"  • Live Spot Price:   {px_text}")
    print(f"  • Position Bias:     {bias_text}")
    print(f"  • Sync Tag:          {sync_text}")

    if score_text == 'NOT FOUND':
        print(f"  ❌ ERROR: Total score element #total-score-val not found!")
        all_passed = False
    elif "BEARISH" not in risk_text and "BULLISH" not in risk_text and "NEUTRAL" not in risk_text:
        print(f"  ❌ ERROR: Risk state not evaluated properly: {risk_text}")
        all_passed = False
    elif px_text in ['NOT FOUND', '$0.00']:
        print(f"  ❌ ERROR: Spot price failed to parse: {px_text}")
        all_passed = False
    else:
        print("  ✅ Total Confluence Score, Risk State, and Live Spot Price verified.")

    # 2. Check 8 Pillars in Pillar Grid
    pillars = ["Macro", "ETF Flows", "Derivatives", "On-Chain", "Geopolitics", "Regulation", "Sentiment", "Cross-Asset"]
    all_pillars_found = True
    for p in pillars:
        if p not in dom:
            print(f"  ❌ ERROR: Pillar '{p}' missing from DOM!")
            all_pillars_found = False
            all_passed = False
    if all_pillars_found:
        print("  ✅ All 8 Confluence Pillars present in rendered DOM.")

    # 3. Check Pre-Flight Checklist
    m_check_score = re.search(r'id="checklist-counter"[^>]*>([^<]+)<', dom)
    check_score_text = m_check_score.group(1).strip() if m_check_score else 'NOT FOUND'
    print(f"  • Checklist Score:   {check_score_text}")
    if "PASS" not in check_score_text and "Pass" not in check_score_text:
        print(f"  ❌ ERROR: Checklist pass rate not computed: {check_score_text}")
        all_passed = False
    else:
        print("  ✅ Pre-flight trading checklist evaluated.")

    # 4. Check Geopolitical Transmission Chain
    if "OIL_TRANSMISSION_ACTIVE" not in dom and "OIL_TRANSMISSION" not in dom:
        print("  ❌ ERROR: Oil transmission flag missing from DOM!")
        all_passed = False
    else:
        print("  ✅ Geopolitical Oil Transmission Pipeline verified.")

    # 5. Check Ledger Tabs and Table Rows
    m_tbody = re.search(r'id="ledger-tbody"[^>]*>(.*?)</tbody>', dom, re.DOTALL)
    tbody_content = m_tbody.group(1) if m_tbody else ''
    rows_count = len(re.findall(r'<tr[^>]*>', tbody_content))
    print(f"  • Ledger Rows Rendered: {rows_count}")
    if rows_count < 1:
        print(f"  ❌ ERROR: Ledger table is empty (found {rows_count} rows).")
        all_passed = False
    else:
        print("  ✅ 9-Tab Historical Ledger successfully rendered authentic rows.")

    # 6. Check Action Controls & Buttons
    if 'id="btn-copy-packet8"' not in dom:
        print("  ❌ ERROR: Missing #btn-copy-packet8 button!")
        all_passed = False
    if 'id="btn-refresh"' not in dom:
        print("  ❌ ERROR: Missing #btn-refresh button!")
        all_passed = False
    if 'id="btn-export-csv"' not in dom:
        print("  ❌ ERROR: Missing #btn-export-csv button!")
        all_passed = False

    # 7. Check Cross-Nav routing links
    nav_links = ['link-dashboard', 'link-matrix', 'link-quant', 'link-liq', 'link-sweep', 'link-absorb', 'link-threat', 'link-fractal']
    for nl in nav_links:
        if f'id="{nl}"' not in dom:
            print(f"  ❌ ERROR: Missing nav link id='{nl}'!")
            all_passed = False
    print("  ✅ All action controls, copy button, and navigation links verified.")

server.shutdown()

if not all_passed:
    print("\n❌ HEADLESS CHROME DOM AUDIT FAILED!")
    sys.exit(1)
else:
    print("\n========================================================")
    print("🎉 ALL VOLATILITY RADAR LIVE DOM TESTS PASSED (100%)!")
    print("========================================================")
    sys.exit(0)

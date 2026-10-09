#!/usr/bin/env python3
"""
Test Threat Matrix Pro DOM & Telemetry Execution via Headless Chrome
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
PORT = 8127

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

server = HTTPServer(('127.0.0.1', PORT), QuietHandler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()

print(f"Local test server running at http://127.0.0.1:{PORT}/")

test_urls = [
    f"http://127.0.0.1:{PORT}/threat-matrix/",
    f"http://127.0.0.1:{PORT}/threat-matrix.html"
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

    # 1. Check Threat Score & Status
    m_score = re.search(r'id="threat-score"[^>]*>([^<]+)<', dom)
    score_text = m_score.group(1).strip() if m_score else 'NOT FOUND'

    m_status = re.search(r'id="threat-status"[^>]*>([^<]+)<', dom)
    status_text = m_status.group(1).strip() if m_status else 'NOT FOUND'

    m_action = re.search(r'id="threat-action"[^>]*>([^<]+)<', dom)
    action_text = m_action.group(1).strip() if m_action else 'NOT FOUND'

    m_px = re.search(r'id="px-live"[^>]*>([^<]+)<', dom)
    px_text = m_px.group(1).strip() if m_px else 'NOT FOUND'

    m_sync = re.search(r'id="threat-sync-tag"[^>]*>([^<]+)<', dom)
    sync_text = m_sync.group(1).strip() if m_sync else 'NOT FOUND'

    print(f"  • Composite Threat Score: {score_text}")
    print(f"  • Threat Status:          {status_text}")
    print(f"  • Live Spot Price:        {px_text}")
    print(f"  • Tactical Action:        {action_text}")
    print(f"  • Sync Tag Status:        {sync_text}")

    score_num = int(re.sub(r'[^0-9]', '', score_text)) if re.sub(r'[^0-9]', '', score_text) else 0
    if score_num < 66:
        print(f"  ❌ ERROR: Unexpected threat score: {score_text} (expected >= 66% Crimson Gate)")
        all_passed = False
    elif "CRITICAL" not in status_text:
        print(f"  ❌ ERROR: Threat status not evaluated properly: {status_text}")
        all_passed = False
    elif px_text in ['NOT FOUND', '$0.00']:
        print(f"  ❌ ERROR: Spot price failed to parse: {px_text}")
        all_passed = False
    else:
        print("  ✅ Threat Score, Status, and Spot Price verified.")

    # 2. Check 4 Core Module Metrics
    metrics = {
        'val-ratio': 'SPX/RSP Ratio',
        'val-yield': 'US 10Y Yield',
        'val-mstr': 'MSTR Price',
        'val-season': 'Seasonality State'
    }
    for metric_id, desc in metrics.items():
        m_val = re.search(rf'id="{metric_id}"[^>]*>([^<]+)<', dom)
        val = m_val.group(1).strip() if m_val else 'EMPTY'
        print(f"  • Metric [{desc:<18}]: {val}")
        if val in ['EMPTY', 'loading', '...']:
            print(f"  ❌ ERROR: Metric {metric_id} is unpopulated!")
            all_passed = False

    # 3. Check Canvas Chart
    if 'id="macroChart"' not in dom:
        print("  ❌ ERROR: macroChart canvas missing from rendered DOM!")
        all_passed = False
    else:
        print("  ✅ Macro Canvas Chart present in DOM.")

    # 4. Check Copy Packet 7 Button
    if 'id="btn-copy-packet7"' not in dom:
        print("  ❌ ERROR: Copy Packet 7 button missing!")
        all_passed = False
    else:
        print("  ✅ Copy Data Packet 7 button present.")

    # 5. Check Navigation Links
    for nav_id in ['link-dashboard', 'link-matrix', 'link-quant', 'link-liq', 'link-sweep', 'link-absorb', 'link-fractal']:
        if f'id="{nav_id}"' not in dom:
            print(f"  ❌ ERROR: Navigation link {nav_id} missing!")
            all_passed = False
    print("  ✅ All 7 navbar cross-links verified.")

server.shutdown()

if all_passed:
    print("\n========================================================")
    print("🎉 ALL THREAT MATRIX LIVE DOM TESTS PASSED (100% SUCCESS)!")
    print("========================================================")
    sys.exit(0)
else:
    print("\n❌ SOME TESTS FAILED.")
    sys.exit(1)

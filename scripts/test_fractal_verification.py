#!/usr/bin/env python3
"""
Comprehensive Headless Chrome & DOM Verification for fractal.html
Nexus Terminal — BTC Fractal Lab
"""

import sys
import os
import time
import subprocess
import http.server
import socketserver
import threading
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fractal_path = os.path.join(repo_root, "fractal.html")

print("=== 1. VERIFYING FRACTAL.HTML SOURCE INTEGRITY ===")
with open(fractal_path, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Strict check: Zero Math.random() in code
# Check if Math.random() is invoked anywhere
if re.search(r'Math\.random\s*\(', html):
    print("❌ FAILED: Found Math.random() invocation in fractal.html!")
    sys.exit(1)
else:
    print("✓ Zero Math.random() invocations confirmed.")

# 2. Check for required elements
req_elements = [
    'id="fractal-sync-tag"',
    'id="fractal-staleness-banner"',
    'id="live-btc-spot"',
    'id="live-curr-corr"',
    'id="void-status-pill"',
    'id="bars"',
    'id="analogs-body"',
    'setInterval(refreshLive, 10000)'
]
for req in req_elements:
    if req not in html:
        print(f"❌ FAILED: Missing element {req} in fractal.html!")
        sys.exit(1)
    else:
        print(f"✓ Found {req}")

# 3. Spin up local HTTP server and test via headless Chrome
print("\n=== 2. RUNNING HEADLESS CHROME DOM DUMP ===")
PORT = 8912
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=repo_root, **kwargs)
    def log_message(self, format, *args):
        pass

server = socketserver.TCPServer(("", PORT), Handler)
server_thread = threading.Thread(target=server.serve_forever, daemon=True)
server_thread.start()
print(f"✓ Local server listening at http://localhost:{PORT}")

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
url = f'http://localhost:{PORT}/fractal.html'

cmd = [chrome_path, '--headless=new', '--dump-dom', '--virtual-time-budget=5000', url]

try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=20, encoding='utf-8')
    dom = res.stdout
    print(f"✓ Headless Chrome dumped DOM: {len(dom)} characters")

    # Verify elements in the rendered DOM
    dom_checks = [
        ('twins-count', r'<div id="twins-count"[^>]*>(\d+)</div>', 'Twins count'),
        ('live-btc-spot', r'<div id="live-btc-spot"[^>]*>([^<]+)</div>', 'Live Spot Price'),
        ('live-curr-corr', r'<div id="live-curr-corr"[^>]*>([^<]+)</div>', 'Live 4H Correlation'),
        ('void-status-pill', r'<span id="void-status-pill"[^>]*>([^<]+)</span>', 'Void Status Pill'),
        ('fractal-sync-tag', r'<span id="fractal-sync-tag"[^>]*>([^<]+)</span>', 'Sync Tag')
    ]

    for elem_id, pattern, label in dom_checks:
        m = re.search(pattern, dom)
        if m:
            print(f"  ✓ {label}: {m.group(1).strip()}")
        else:
            print(f"  ❌ FAILED: Could not match {label} (id={elem_id}) in DOM!")
            sys.exit(1)

    # Check 120 bars rendered inside #bars
    bars_match = re.search(r'<div id="bars"[^>]*>(.*?)</div>\s*<div style="display:flex; justify-content:space-between;', dom, re.DOTALL)
    if bars_match:
        bars_html = bars_match.group(1)
        bar_count = len(re.findall(r'<div class="bar"', bars_html))
        print(f"  ✓ Rendered Bar Elements in #bars: {bar_count}")
        if bar_count != 120:
            print(f"  ❌ Expected 120 template bars in initial paint, found {bar_count}!")
            sys.exit(1)
    else:
        print("  ❌ Failed to extract #bars container!")
        sys.exit(1)

    # Check 17 analog rows inside #analogs-body
    tbody_match = re.search(r'<tbody id="analogs-body">(.*?)</tbody>', dom, re.DOTALL)
    if tbody_match:
        tbody_html = tbody_match.group(1)
        row_count = len(re.findall(r'<tr class="analog-row', tbody_html))
        print(f"  ✓ Rendered Top Analogs Rows: {row_count}")
        if row_count != 17:
            print(f"  ❌ Expected 17 analog rows, found {row_count}!")
            sys.exit(1)
    else:
        print("  ❌ Failed to extract #analogs-body rows!")
        sys.exit(1)

    print("\n✅ ALL DOM & BROWSER VERIFICATIONS PASSED SUCCESSFULLY!")

except Exception as e:
    print(f"\n❌ Browser test error: {e}")
    sys.exit(1)
finally:
    server.shutdown()

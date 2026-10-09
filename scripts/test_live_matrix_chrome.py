import http.server
import socketserver
import subprocess
import threading
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

PORT = 8765
DIRECTORY = r'C:\Users\aikel\pcf3-v9-nexus'

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    def log_message(self, format, *args):
        pass # Silence server logs

httpd = socketserver.TCPServer(("", PORT), Handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
print(f"Local test server started on http://localhost:{PORT}")

time.sleep(1)

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
url = f'http://localhost:{PORT}/matrix.html'

cmd = [chrome_path, '--headless=new', '--dump-dom', url]

print("Launching Chrome headless to dump DOM...")
try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=20, encoding='utf-8')
    dom = res.stdout
    print(f"Dumped DOM length: {len(dom)} characters")

    # Tests
    checks = [
        ("Staleness banner exists in DOM", 'id="radar-staleness-banner"' in dom),
        ("Sync pill exists in DOM", 'id="radar-sync-pill"' in dom),
        ("Dynamic sync pill text present", '● SYNCED' in dom or '⚠️ STALE' in dom),
        ("Active regime card", 'HEALTHY BASE BUILDING' in dom or 'HEALTHY BULL' in dom or 'CONFIG' in dom),
        ("Tactical Execution Matrix", 'TACTICAL EXECUTION' in dom),
        ("55 Sensors Table", '55 / 55 SENSORS ACTIVE' in dom),
        ("POC Live Value", '$84,100' in dom),
        ("VAH Live Value", '$86,300' in dom),
        ("STH Cost Basis Live Value", '$73,935' in dom),
        ("50D EMA Live Value", '$79,774' in dom),
        ("ETF 3D Live Value", '-$610.2M' in dom),
        ("ETF 7D Live Value", '-$556.1M' in dom),
        ("Global L/S Ratio Live Value", '1.710 Ratio' in dom),
        ("Futures Taker Ratio Live Value", '2.765 Ratio' in dom),
        ("LTH Realized Price Live Value", '$42,058' in dom),
        ("DXY Live Value", '102.09' in dom),
        ("US10Y Live Value", '5.23%' in dom)
    ]

    all_passed = True
    print("\n=== VERIFICATION RESULTS ===")
    for desc, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed: all_passed = False
        print(f"  {status}: {desc}")

    if all_passed:
        print("\n🎉 ALL LIVE MATRIX DOM VERIFICATIONS PASSED!")
    else:
        print("\n⚠️ SOME CHECKS FAILED - INSPECTING DOM")

except Exception as e:
    print(f"Execution failed: {e}")
finally:
    httpd.shutdown()
    print("Server stopped.")

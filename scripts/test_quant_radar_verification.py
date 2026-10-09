import http.server
import socketserver
import subprocess
import threading
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

PORT = 8771
DIRECTORY = r'C:\Users\aikel\pcf3-v9-nexus'

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    def log_message(self, format, *args):
        pass

httpd = socketserver.TCPServer(("", PORT), Handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
print(f"Server started on http://localhost:{PORT}")

time.sleep(1)
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

targets = [
    ('quant-radar/index.html', f'http://localhost:{PORT}/quant-radar/index.html'),
    ('quant-radar.html', f'http://localhost:{PORT}/quant-radar.html')
]

overall_pass = True

try:
    for name, url in targets:
        print(f"\n--- Testing {name} ---")
        cmd = [chrome_path, '--headless=new', '--dump-dom', '--virtual-time-budget=4000', url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding='utf-8')
        dom = res.stdout
        print(f"Dumped DOM length: {len(dom)}")

        checks = [
            ("Staleness banner exists in DOM", 'id="quant-staleness-banner"' in dom),
            ("Sync tag exists in DOM", 'id="quant-sync-tag"' in dom),
            ("Sync tag live status", '● LIVE STREAMING' in dom or '⚠️ CACHED SNAPSHOT' in dom),
            ("Price header populated", 'id="live-price-header"' in dom and 'Loading...' not in dom),
            ("Card A 200 SMA populated", 'id="val-sma200"' in dom and 'val-sma200">$' in dom),
            ("Card A 200 SMA slope status", 'val-sma200-slope">' in dom),
            ("Card A regime badge", 'REGIME EXPANDING' in dom or 'REGIME DEFENSIVE' in dom),
            ("Card B 21 EMA populated", 'id="val-ema21"' in dom and 'val-ema21">$' in dom),
            ("Card B 14 RSI populated", 'id="val-rsi14"' in dom and 'val-rsi14">-' not in dom),
            ("Card B 20 ATR populated", 'id="val-atr20"' in dom and 'val-atr20">$' in dom),
            ("Card B setup badge", 'SETUP READY' in dom or 'WAIT' in dom),
            ("Card C 30D POC populated", 'id="val-poc30d"' in dom and 'val-poc30d">$' in dom),
            ("Card C location badge", 'LOCATION GOOD' in dom or 'ABOVE VALUE' in dom),
            ("Master signal banner", 'id="master-signal-banner"' in dom),
            ("Risk Initial Stop populated", 'id="ref-init-stop"' in dom and 'style="color:var(--red-bright);">-<' not in dom),
            ("Risk Trail Stop populated", 'id="ref-trail-stop"' in dom and 'style="color:var(--green-bright);">-<' not in dom),
            ("Risk Failsafe Stop populated", 'id="ref-failsafe-stop"' in dom and 'style="color:var(--amber-bright);">-<' not in dom),
            ("No stale derivatives footer", "quant radar provides objective 3-rule" in dom.lower()),
            ("Auto-refresh loop present", "setInterval(fetchAndCompute, 10000)" in dom)
        ]

        target_pass = True
        for desc, ok in checks:
            status = "✅ PASS" if ok else "❌ FAIL"
            if not ok: 
                target_pass = False
                overall_pass = False
            print(f"  {status}: {desc}")

        if target_pass:
            print(f"  🎉 {name} passed all checks!")
        else:
            print(f"  ⚠️ {name} has failing checks!")

    if overall_pass:
        print("\n🎉 ALL QUANT RADAR TARGETS PASSED 100%!")
    else:
        print("\n⚠️ SOME CHECKS FAILED ACROSS TARGETS!")

except Exception as e:
    print("Execution failed:", e)
finally:
    httpd.shutdown()
    print("Server stopped.")

import http.server
import socketserver
import subprocess
import threading
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

PORT = 8773
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
    ('liquidity-radar/index.html', f'http://localhost:{PORT}/liquidity-radar/index.html'),
    ('liquidity-radar.html', f'http://localhost:{PORT}/liquidity-radar.html')
]

overall_pass = True

try:
    for name, url in targets:
        print(f"\n--- Testing {name} ---")
        cmd = [chrome_path, '--headless=new', '--dump-dom', '--virtual-time-budget=4500', url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding='utf-8')
        dom = res.stdout
        print(f"Dumped DOM length: {len(dom)}")

        checks = [
            ("Staleness banner exists in DOM", 'id="liquidity-staleness-banner"' in dom),
            ("Sync tag exists in DOM", 'id="liquidity-sync-tag"' in dom),
            ("Sync tag live status active", '● LIVE STREAMING' in dom or '⚠️ STALE SNAPSHOT' in dom or '⚠️ LOCAL FAILOVER' in dom),
            ("Spot price populated", 'id="kpi-spot"' in dom and '—' not in dom.split('id="kpi-spot">')[1].split('<')[0]),
            ("50-Week MA populated", 'id="kpi-50w"' in dom and '—' not in dom.split('id="kpi-50w">')[1].split('<')[0]),
            ("200-Day SMA populated", 'id="kpi-200d"' in dom and '—' not in dom.split('id="kpi-200d">')[1].split('<')[0]),
            ("Funding rate populated", 'id="kpi-funding"' in dom and '—' not in dom.split('id="kpi-funding">')[1].split('<')[0]),
            ("Open interest populated", 'id="kpi-oi"' in dom and 'BTC' in dom.split('id="kpi-oi">')[1].split('<')[0]),
            ("DXY live value populated", '102.09' in dom),
            ("ETF 7D real value populated (-$556.1M)", '-$556.1M' in dom or '-556.1' in dom),
            ("No stale prototype ETF +$218.4M", '+$218.4M' not in dom),
            ("Card B 30D POC populated", 'id="g-poc-val"' in dom and '$8' in dom.split('id="g-poc-val">')[1].split('<')[0]),
            ("Card B Value Area populated", 'id="g-va-val"' in dom and '–' in dom.split('id="g-va-val">')[1].split('<')[0]),
            ("Psych Support & Resistance mapped", '$80,000' in dom and '$85,000' in dom),
            ("4H Market structure populated", 'id="h-structure-val"' in dom),
            ("Protocol State & Score populated", 'id="kpi-state"' in dom and 'EVALUATING' not in dom.split('id="kpi-state"')[1].split('<')[0]),
            ("3-Bucket capital architecture active", '3-BUCKET DISCIPLINE ACTIVE' in dom),
            ("Auto-refresh loop present (10s)", 'setInterval(fetchAndComputeAll, 10000)' in dom)
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
        print("\n🎉 ALL LIQUIDITY RADAR TARGETS PASSED 100%!")
    else:
        print("\n⚠️ SOME CHECKS FAILED ACROSS TARGETS!")

except Exception as e:
    print("Execution failed:", e)
finally:
    httpd.shutdown()
    print("Server stopped.")

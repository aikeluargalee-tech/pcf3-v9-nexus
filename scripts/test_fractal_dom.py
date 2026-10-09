import http.server
import socketserver
import subprocess
import threading
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

PORT = 8774
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
url = f'http://localhost:{PORT}/fractal.html'

cmd = [chrome_path, '--headless=new', '--dump-dom', '--virtual-time-budget=4000', url]

try:
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, encoding='utf-8')
    dom = res.stdout
    print(f"Dumped DOM length: {len(dom)}")

    # Check key elements in DOM
    checks = [
        'twins-count', 'fwd-1w', 'fwd-2w', 'win-rate',
        'analogs-body', 'bars'
    ]

    for c in checks:
        for line in dom.splitlines():
            if f'id="{c}"' in line or f'id=\'{c}\'' in line:
                print(f"  {c}: {line.strip()[:100]}")
                break

except Exception as e:
    print("Execution failed:", e)
finally:
    httpd.shutdown()
    print("Server stopped.")

import sys
import io
import subprocess
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
url = 'https://aikeluargalee-tech.github.io/pcf3-v9-nexus/fractal.html'
cmd = [chrome_path, '--headless=new', '--dump-dom', '--virtual-time-budget=6000', url]

res = subprocess.run(cmd, capture_output=True, text=True, timeout=25, encoding='utf-8')
dom = res.stdout
print(f'Dumped live DOM length: {len(dom)}')

patterns = [
    (r'<div id="live-btc-spot"[^>]*>([^<]+)</div>', 'Live Spot Price'),
    (r'<div id="live-curr-corr"[^>]*>([^<]+)</div>', 'Live 4H Correlation'),
    (r'<span id="void-status-pill"[^>]*>([^<]+)</span>', 'Void Status Pill'),
    (r'<span id="fractal-sync-tag"[^>]*>([^<]+)</span>', 'Sync Tag'),
    (r'<div id="twins-count"[^>]*>(\d+)</div>', 'Twins Count'),
]

for pat, label in patterns:
    m = re.search(pat, dom)
    if m:
        print(f'  ✓ {label}: {m.group(1).strip()}')
    else:
        print(f'  ❌ Missing: {label}')

bar_count = len(re.findall(r'<div class="bar"', dom))
print(f'  ✓ Rendered Bar Elements in DOM: {bar_count}')

row_count = len(re.findall(r'<tr class="analog-row', dom))
print(f'  ✓ Rendered Top Analogs Rows: {row_count}')

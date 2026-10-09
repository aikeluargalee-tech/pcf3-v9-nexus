import sys
import io
import subprocess
import re
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
url = 'https://nexus-analysis.github.io/btc-sweep-desk/'

print("=== 1. FETCHING RAW HTML FROM GITHUB PAGES ===")
r = requests.get(url, timeout=10)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

print("\n=== 2. RUNNING HEADLESS CHROME DOM & CONSOLE AUDIT ===")
cmd = [chrome_path, '--headless=new', '--dump-dom', '--virtual-time-budget=6000', url]

res = subprocess.run(cmd, capture_output=True, text=True, timeout=25, encoding='utf-8')
dom = res.stdout
print(f"Rendered live DOM length: {len(dom)}")

for tag in ['px', 'call', 'why', 'spot', 'action', 'asof', 'next', 'etfnote']:
    m = re.search(rf'id="{tag}"[^>]*>([^<]+)<', dom)
    if m:
        print(f"  {tag:<10}: {m.group(1).strip()}")
    else:
        print(f"  {tag:<10}: NOT FOUND / EMPTY")

# Check level rows
levels = re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td><td class="([^"]*)">(.*?)</td></tr>', dom)
print(f"\nRendered Levels ({len(levels)} rows):")
for lvl in levels:
    print(f"  • {lvl[0]:<20} | Price: {lvl[1]:<10} | State: {lvl[3]}")

# Check checks list
checks = re.findall(r'<li><b class="([^"]*)">(.*?)</b> — (.*?)</li>', dom)
print(f"\nRendered Checklist ({len(checks)} items):")
for chk in checks:
    print(f"  • [{chk[0].upper()}] {chk[2]}: {chk[1]}")

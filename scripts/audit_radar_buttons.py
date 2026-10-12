import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

radars = [
    ('Main Terminal (Home)', 'index.html'),
    ('Regime Radar', 'matrix.html'),
    ('Quant Radar (Subdir)', 'quant-radar/index.html'),
    ('Quant Radar (Root Mirror)', 'quant-radar.html'),
    ('Liquidity Radar (Subdir)', 'liquidity-radar/index.html'),
    ('Liquidity Radar (Root Mirror)', 'liquidity-radar.html'),
    ('Sweep Desk Pro (Subdir)', 'sweep-desk/index.html'),
    ('Sweep Desk Pro (Root Mirror)', 'sweep-desk.html'),
    ('Absorption Radar Pro (Subdir)', 'absorption-radar/index.html'),
    ('Absorption Radar Pro (Root Mirror)', 'absorption-radar.html'),
    ('Threat Matrix Pro (Subdir)', 'threat-matrix/index.html'),
    ('Threat Matrix Pro (Root Mirror)', 'threat-matrix.html'),
    ('BTC Volatility Radar Pro (Subdir)', 'volatility-radar/index.html'),
    ('BTC Volatility Radar Pro (Root Mirror)', 'volatility-radar.html'),
    ('Fractal Lab', 'fractal.html')
]

print("=== RADAR PAGES BUTTON AUDIT ===")
all_passed = True
for name, rel_path in radars:
    path = os.path.join(repo, rel_path)
    if not os.path.exists(path):
        print(f"❌ {name}: {rel_path} NOT FOUND")
        all_passed = False
        continue
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Find standard HTML buttons
    raw_buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.DOTALL | re.IGNORECASE)
    cleaned_buttons = [re.sub(r'<[^>]+>', '', b).strip() for b in raw_buttons]

    # Refresh checks
    refresh_list = [b for b in cleaned_buttons if any(k in b.lower() for k in ['refresh', 'sync', 'update', 'reload'])]
    has_refresh_fn = any(fn in html for fn in ['loadLive', 'fetchLive', 'refresh', 'fetchTelemetry', 'Force Refresh', 'cf()', 'refreshLive'])

    # Copy checks
    copy_list = [b for b in cleaned_buttons if any(k in b.lower() for k in ['copy', 'packet'])]
    has_copy_fn = any(fn in html for fn in ['copyData', 'copyPacket', 'navigator.clipboard', 'execCommand', 'copyFractalData'])

    # React JSX checks in index.html
    if rel_path == 'index.html':
        if '🔄 Refresh Live' in html:
            refresh_list.append('🔄 Refresh Live')
        if 'Force Refresh Now' in html:
            refresh_list.append('🔄 Force Refresh Now')
        if '📋 Copy Full Packet' in html:
            copy_list.append('📋 Copy Full Packet')

    has_refresh = bool(refresh_list) and has_refresh_fn
    has_copy = bool(copy_list) and has_copy_fn

    status = "✅ PASS" if (has_refresh and has_copy) else "❌ FAIL"
    if not (has_refresh and has_copy):
        all_passed = False

    print(f"\n--- {name} ({rel_path}) --- {status}")
    print(f"  Refresh Controls: {refresh_list if refresh_list else 'NONE'} (Active Fn: {has_refresh_fn})")
    print(f"  Copy Controls:    {copy_list if copy_list else 'NONE'} (Active Fn: {has_copy_fn})")

print("\n" + "="*50)
if all_passed:
    print("🎯 ALL 9 RADAR DESKS & MIRRORS VERIFIED: BOTH REFRESH AND COPY BUTTONS PRESENT & ACTIVE")
    sys.exit(0)
else:
    print("❌ AUDIT FAILED: ONE OR MORE RADAR DESKS MISSING CONTROLS")
    sys.exit(1)

import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('matrix.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find JS section
js_match = re.search(r'<script>(.*?)</script>', text, re.DOTALL)
js_code = js_match.group(1) if js_match else ''

rows = re.findall(r'<tr class="telemetry-row"[^>]*>(.*?)</tr>', text, re.DOTALL)
print(f"Total telemetry rows in HTML: {len(rows)}")

updated_count = 0
not_updated = []

for i, r in enumerate(rows):
    num_m = re.search(r'>(\d+)</td>', r)
    num = num_m.group(1) if num_m else str(i+1)
    name_m = re.search(r'<div class="telemetry-name">(.*?)</div>', r)
    name = name_m.group(1) if name_m else 'Unknown'
    id_m = re.findall(r'id="([^"]+)"', r)
    
    # Check if this row is updated in JS either via metric ID or via live-row-N
    is_updated = any(x in js_code for x in id_m) or f"live-row-{num}" in js_code
    if is_updated:
        updated_count += 1
    else:
        not_updated.append((num, name, id_m))

print(f"✅ Dynamically bound sensors in JS: {updated_count} / {len(rows)}")
if not_updated:
    print(f"❌ Sensors not bound in JS:")
    for num, name, id_m in not_updated:
        print(f"  Row {num}: {name} -> {id_m}")
else:
    print("🎯 ALL 55 SENSORS ARE 100% DYNAMICALLY BOUND IN JAVASCRIPT!")

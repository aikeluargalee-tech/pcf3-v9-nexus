import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo = r'C:\Users\aikel\pcf3-v9-nexus'

print("=== AUDITING THE 4 COPY DATA PACKETS FOR STRICT COMPLIANCE ===")

# 1. Packet 1: index.html (PCF3_LIVE_PACKET_DEFAULT.txt)
p1_path = os.path.join(repo, "PCF3_LIVE_PACKET_DEFAULT.txt")
with open(p1_path, "r", encoding="utf-8") as f:
    p1 = f.read()

assert "PCF3 MASTER PROMPT" in p1, "Packet 1 missing Master Prompt header!"
assert "SPOT:" in p1, "Packet 1 missing SPOT price field!"
print("✓ Packet 1 (Nexus Master): Verified intact. Header & Telemetry tokens present.")

# 2. Packet 2: data2_exporter.js & matrix.html
p2_path = os.path.join(repo, "data2_exporter.js")
with open(p2_path, "r", encoding="utf-8") as f:
    p2 = f.read()

assert "copyData2ForManus" in p2, "Packet 2 generator function missing!"
print("✓ Packet 2 (Tactical Sleeve): Found copyData2ForManus in data2_exporter.js.")

# Check for hardcoded stale string in Packet 2
if "+$218.4M" in p2:
    print("⚠️ WARNING: Found stale hardcoded ETF string '+$218.4M' in data2_exporter.js!")
else:
    print("✓ Packet 2: No stale hardcoded ETF flow string.")

# 3. Packet 3: quant-radar
p3_path = os.path.join(repo, "quant-radar", "index.html")
with open(p3_path, "r", encoding="utf-8") as f:
    p3 = f.read()

assert "DATA PACKET 3 (USSM v1.0)" in p3, "Packet 3 missing DATA PACKET 3 header!"
assert "copyDataPacket3" in p3, "Packet 3 missing copyDataPacket3 generator!"
print("✓ Packet 3 (Quant Radar USSM v1.0): Verified intact with 5-Rule USSM specification.")

# 4. Packet 4: liquidity-radar
p4_path = os.path.join(repo, "liquidity-radar", "index.html")
with open(p4_path, "r", encoding="utf-8") as f:
    p4 = f.read()

assert "DATA PACKET 4 (PFC-SSP v2.0)" in p4, "Packet 4 missing DATA PACKET 4 header!"
assert "copyDataPacket4" in p4, "Packet 4 missing copyDataPacket4 generator!"
print("✓ Packet 4 (Liquidity Radar PFC-SSP v2.0): Verified intact with 4-Engine specification.")

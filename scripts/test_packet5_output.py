#!/usr/bin/env python3
"""
Verify DATA PACKET 5 format and content completeness
Nexus Terminal — PCF3
"""
import sys
import subprocess
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(repo_root, "sweep-desk", "index.html"), "r", encoding="utf-8") as f:
    html = f.read()

# Extract copyDataPacket5 function
m = re.search(r'async function copyDataPacket5\(\)\s*\{(.*?)\n\}', html, re.DOTALL)
if not m:
    print("❌ Failed to find copyDataPacket5 function in sweep-desk/index.html")
    sys.exit(1)

func_code = m.group(0)

# Verify key guardrails in copyDataPacket5
required_tokens = [
    "DATA PACKET 5 (SMC-SWEEP v1.0)",
    "BTCUSDT SPOT SWEEP DESK REVIEW PROMPT & DATA PACKET 5",
    "Current BTC Spot Price:",
    "Tactical Call Verdict:",
    "Checklist Score:",
    "Active Monitored Pool:",
    "Recommended Spot Action:",
    "Binance 8h Funding Rate:",
    "24h Open Interest Change:",
    "Spot Taker CVD Since Sweep:",
    "Institutional 7D ETF Net:",
    "4H Volatility ATR(14):",
    "ACTIVE LIQUIDITY POOLS STATUS TABLE",
    "END OF DATA PACKET 5 (SMC-SWEEP v1.0)"
]

missing = []
for tok in required_tokens:
    if tok not in func_code:
        missing.append(tok)

if missing:
    print(f"❌ Missing tokens in copyDataPacket5: {missing}")
    sys.exit(1)
else:
    print("✅ DATA PACKET 5 (SMC-SWEEP v1.0) function verified with all required sections and tokens!")

# Verify in sweep-desk.html as well
with open(os.path.join(repo_root, "sweep-desk.html"), "r", encoding="utf-8") as f:
    mirror_html = f.read()

if "DATA PACKET 5 (SMC-SWEEP v1.0)" not in mirror_html:
    print("❌ DATA PACKET 5 token missing in sweep-desk.html")
    sys.exit(1)
else:
    print("✅ DATA PACKET 5 token verified in sweep-desk.html mirror!")

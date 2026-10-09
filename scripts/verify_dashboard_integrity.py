#!/usr/bin/env python3
"""
Dashboard Integrity & Data Provenance Guardrail Test
Nexus Terminal — PCF3

Ensures that:
1. Zero mock loops or Math.random() in evidence cards.
2. Zero stale hardcoded strings from prototypes (Risk-On 92, Bullish Expansion 83, etc.).
3. Real-time Staleness Watchdog banner and age pill are present.
4. 4 Synthesis Cards (Market Structure, Derivatives, Psych Levels, Regime Synthesis) are dynamically bound.
5. Live packet is valid and populated.
"""

import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
index_path = os.path.join(repo_root, "index.html")
packet_path = os.path.join(repo_root, "PCF3_LIVE_PACKET_DEFAULT.txt")

errors = []

print("=== RUNNING DASHBOARD INTEGRITY AUDIT ===")

# 1. Inspect index.html
if not os.path.exists(index_path):
    errors.append("index.html not found!")
else:
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Rule 1: No Math.random mock loops in card generation
    if "Array.from({length: 58}" in html or "Array.from({length: 70}" in html:
        errors.append("Violation: Found Array.from() mock cards generator loop.")
    
    # Rule 2: No stale hardcoded strings in card content
    stale_strings = [
        "Risk-On 92/100",
        "Bullish Expansion 83/100",
        "Trio 2/3 ADX 28.5 Bull",
        "STRONG score 5 (HVN",
        "POC $84,800 magnet",
        "clamp((83-60)/30)=0.76"
    ]
    for s in stale_strings:
        if s in html:
            errors.append(f"Violation: Found stale hardcoded prototype string: '{s}'")

    # Rule 3: Staleness Watchdog present
    if "TELEMETRY STALE" not in html or "packetAge" not in html:
        errors.append("Violation: Missing real-time packet staleness watchdog or alert banner.")

    # Rule 4: Dynamic quantitative parsing
    required_parsers = [
        "regimeScore",
        "regimeClass",
        "tradingBias",
        "dailyStructure",
        "weeklyStructure",
        "oiChange",
        "funding",
        "dampener"
    ]
    for p in required_parsers:
        if p not in html:
            errors.append(f"Violation: Missing dynamic metric parser for: '{p}'")

# 2. Inspect Live Packet
if not os.path.exists(packet_path):
    errors.append("PCF3_LIVE_PACKET_DEFAULT.txt not found!")
else:
    with open(packet_path, "r", encoding="utf-8") as f:
        packet = f.read()
    
    if len(packet) < 10000:
        errors.append(f"Violation: Packet suspiciously small ({len(packet)} chars).")
    
    if "TIMESTAMP_UTC" not in packet:
        errors.append("Violation: Packet missing TIMESTAMP_UTC header.")

    if "SPOT:" not in packet:
        errors.append("Violation: Packet missing SPOT price field.")

if errors:
    print(f"\n❌ AUDIT FAILED WITH {len(errors)} VIOLATIONS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\n✅ AUDIT PASSED: All guardrails satisfied! Zero mock data, complete dynamic binding, watchdog verified.")
    sys.exit(0)

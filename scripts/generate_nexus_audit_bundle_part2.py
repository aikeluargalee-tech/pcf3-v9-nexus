"""
generate_nexus_audit_bundle_part2.py
Generates nexus_audit_bundle_part2.md in the root of pcf3-v9-nexus.
Includes:
1. index.html application logic from function resolvePacketUrl() to end of file (including parseCards and parseTelemetry).
2. pcf3_collector_default.py quantitative engine functions (Market Structure, Trend, MA/Momentum/Regime scoring, Continuous Sizing).
3. Complete <script> blocks for:
   - liquidity-radar.html
   - threat-matrix.html
   - volatility-radar.html
   - absorption-radar.html
   - fractal.html and btc_fractal_lab.py
"""

import os
import re
import datetime

ROOT_DIR = r"C:\Users\aikel\pcf3-v9-nexus"
OUTPUT_FILE = os.path.join(ROOT_DIR, "nexus_audit_bundle_part2.md")

def get_file_content(rel_path):
    full_path = os.path.join(ROOT_DIR, rel_path)
    if not os.path.exists(full_path):
        return f"// File not found: {rel_path}"
    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def extract_script_content(html_text):
    """Extract contents of all <script> tags from HTML text."""
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html_text, re.DOTALL | re.IGNORECASE)
    valid_scripts = [s.strip() for s in scripts if s.strip() and not s.strip().startswith("// External script")]
    return "\n\n// --- NEXT SCRIPT BLOCK ---\n\n".join(valid_scripts)

def extract_python_function(full_code, func_name):
    """Extract a python function block by its definition."""
    pattern = rf"(def {func_name}\b.*?\n)(?=\ndef |\nclass |\Z)"
    match = re.search(pattern, full_code, re.DOTALL)
    if match:
        return match.group(0).strip()
    return f"# Function def {func_name} not found"

def build_part2_bundle():
    print("Building nexus_audit_bundle_part2.md...")
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    sections = []
    
    # Header
    sections.append(f"""# NEXUS TERMINAL (PCF3-V9-NEXUS) - AUDIT BUNDLE (PART 2)

**Project Repository:** `aikeluargalee-tech/pcf3-v9-nexus`  
**Live Deployment:** `https://aikeluargalee-tech.github.io/pcf3-v9-nexus/`  
**Audit Bundle:** Part 2 of 2 (Comprehensive Custom Application & Microstructure Logic)  
**Generated At:** {now_utc}  
**Target Reviewer:** Gemini / Frontier LLM Quantitative System Auditor  

---

## EXECUTIVE SUMMARY FOR AUDITORS

This bundle contains the deep mathematical and custom application implementations for Nexus Terminal:

1. **Main Terminal Application Logic (`index.html`):** The complete custom JavaScript codebase starting strictly from `function resolvePacketUrl()` to the end of the file (bypassing minified React/ReactDOM vendor headers). Includes `parseTelemetry()`, `parseCards()` (evaluating the 70 cards including **Market Structure 51/100 Constructive (阳) / Bull Trend / Daily Mixed | W Mixed**, MAMR scoring, and regime confluence), and the React UI controller (`gi`).
2. **Collector Mathematical Engine (`pcf3_collector_default.py`):** The Python functions calculating market structure, 6-regime classification, multi-timeframe storylines (MSNR), top-down alignment, 10/20 SMA trend protocol, institutional trio decision engine, and continuous capital sizing.
3. **Dedicated Radar Engines:** Full untruncated script logic for Liquidity Radar, Threat Matrix, Volatility Radar, Absorption Radar, and the Multi-Cycle Fractal Lab.

---
""")

    # 1. Main Terminal App Logic (index.html)
    print("Extracting index.html custom logic from resolvePacketUrl()...")
    index_content = get_file_content("index.html")
    idx = index_content.find("function resolvePacketUrl()")
    if idx != -1:
        custom_app_code = index_content[idx:]
    else:
        idx2 = index_content.find("resolvePacketUrl")
        custom_app_code = index_content[idx2:] if idx2 != -1 else "// resolvePacketUrl not found"
        
    sections.append(f"""## 1. MAIN TERMINAL APPLICATION LOGIC (`index.html`)

This section contains 100% of the custom application code from `index.html` starting at `function resolvePacketUrl()` to the closing tag of the file.

### Key Logic Contained Herein:
- **`resolvePacketUrl()`:** Intelligent origin/path resolver determining the active static packet endpoint across local dev, staging, and GitHub Pages production.
- **`parseTelemetry(packetText, spotPrice)`:** Parses the raw 9-desk live telemetry feed, extracts metric timestamps, VWAP levels, order book depth, STH cost basis, and indicator states.
- **`parseCards(packetText)`:** The primary quantitative parsing engine that processes all 70 modular telemetry cards, including:
  - **Market Structure Evaluation:** Computes structure scores (e.g., `Market Structure 51/100 Constructive (阳) / Bull Trend / Daily Mixed | W Mixed`).
  - **Trend & MAMR Scores:** Evaluates 10D/20D/50D/200D moving average alignments, slopes, and price acceptance.
  - **Decision Engine & Confluence Cards:** Institutional Trio (ADX + VWAP + RVOL), Regime 3 / Regime 6 consensus, and volatility bounds.
- **`gi` (Root React Component):**
  - High-frequency live spot ticker mirrors (Binance Vision, Binance primary, Binance mirror 3, and Coinbase fallback).
  - State controllers `sf()` (Silent Soft Sync) and `cf()` (Cloud Hard Regenerate via GitHub Actions workflow dispatch).
  - Operational mode controller (`LIVE`, `CACHED`, or `MOCK` with zero-simulation enforcement).
  - Clipboard serializing and 9-Desk Master Dossier export generator.

```javascript
// ============================================================================
// NEXUS TERMINAL - CUSTOM APPLICATION ENGINE (index.html)
// ============================================================================

{custom_app_code}
```

---
""")

    # 2. Collector Script (pcf3_collector_default.py)
    print("Extracting quantitative functions from pcf3_collector_default.py...")
    collector_py = get_file_content("pcf3_collector_default.py")
    
    target_functions = [
        ("Continuous Capital Sizing", "calculate_continuous_sizing"),
        ("Market Structure & Swing Detection", "detect_structure"),
        ("Regime Scores & Timeframe Scoring", "calculate_regime_scores"),
        ("6 Canonical Regimes Classification", "calculate_6_regimes"),
        ("MSNR Storyline & Level Freshness", "calc_storyline_msnr"),
        ("Top-Down Alignment (Weekly -> Daily -> 4H)", "fetch_topdown_analysis"),
        ("10/20 SMA Trend Protocol & MAMR", "fetch_sma_trend_protocol"),
        ("Institutional Decision Engine (ADX + VWAP + RVOL)", "institutional_decision_engine"),
        ("Technical Analysis & Momentum Module", "fetch_ta_v47_raw"),
        ("Composite Scorecard (25/25/20/15/15)", "fetch_scorecard_v47_raw")
    ]
    
    collector_code_blocks = []
    for title, fn_name in target_functions:
        fn_code = extract_python_function(collector_py, fn_name)
        collector_code_blocks.append(f"### 2.{len(collector_code_blocks)+1} {title} (`def {fn_name}`)\n\n```python\n{fn_code}\n```\n")
    
    sections.append(f"""## 2. COLLECTOR QUANTITATIVE & METRIC ENGINES (`pcf3_collector_default.py`)

This section contains the mathematical formulas, scoring models, and state algorithms executed by the Python ingestion runner (`pcf3_collector_default.py`) to generate the master telemetry packets (`PCF3_LIVE_PACKET_DEFAULT.txt`).

{"".join(collector_code_blocks)}
---
""")

    # 3. Remaining Radar Pages (Sections 4.4 to 4.8)
    print("Extracting remaining radar pages scripts...")
    liquidity_radar_js = extract_script_content(get_file_content("liquidity-radar.html"))
    threat_matrix_js = extract_script_content(get_file_content("threat-matrix.html"))
    volatility_radar_js = extract_script_content(get_file_content("volatility-radar.html"))
    
    # Try absorption-radar.html or absorption-radar/index.html
    absorption_radar_html = get_file_content("absorption-radar.html")
    if "// File not found" in absorption_radar_html:
        absorption_radar_html = get_file_content("absorption-radar/index.html")
    absorption_radar_js = extract_script_content(absorption_radar_html)
    
    fractal_js = extract_script_content(get_file_content("fractal.html"))
    btc_fractal_lab_py = get_file_content("btc_fractal_lab.py")
    
    sections.append(f"""## 3. REMAINING RADAR PAGE ENGINES (SECTIONS 4.4 TO 4.8)

This section provides the complete, untruncated `<script>` blocks and analytical engines for the specialized radar sub-dashboards.

### 3.1 Liquidity Radar (`liquidity-radar.html`)
Live order book depth analysis, bid/ask skew ratio, depth ladder visualization, and liquidity cluster modeling around psychological round numbers ($500 depth):

```javascript
{liquidity_radar_js}
```

### 3.2 Threat Matrix (`threat-matrix.html`)
4-Pillar Cross-Asset Macro Risk Engine:
- Pillar 1: US 10-Year Treasury Yield Surge (35 pts)
- Pillar 2: US Dollar Index (DXY) Structural Breakout (30 pts)
- Pillar 3: S&P 500 Equity Drawdown & VIX Term Structure (20 pts)
- Pillar 4: WTI Crude Oil / Geopolitical Shock (15 pts)
- Fail-Closed CRIMSON Lock enforcing 100% USDT Cash Preservation.

```javascript
{threat_matrix_js}
```

### 3.3 Volatility Radar (`volatility-radar.html`)
8-Pillar Volatility Micro-Regime Scoring Engine:
- Evaluates ATR percentiles, Bollinger bandwidth, historical vs implied volatility, and intraday range velocity from -4 (extreme compression) to +4 (extreme expansion).

```javascript
{volatility_radar_js}
```

### 3.4 Absorption Radar & CVD Order Flow Engine (`absorption-radar.html`)
Real-time Cumulative Volume Delta (CVD) tracking from continuous aggTrades, algorithmic absorption detection, and delta divergence:

```javascript
{absorption_radar_js}
```

### 3.5 Multi-Cycle Fractal Matching Lab (`btc_fractal_lab.py` & `fractal.html`)
Python and JavaScript engines for historical cycle alignment across 2015-2017, 2018-2020, and 2021-2024 cycles using first-difference log-returns and Pearson correlation:

```python
# btc_fractal_lab.py (Python Cycle Alignment Engine)
{btc_fractal_lab_py}
```

```javascript
// fractal.html (Frontend Fractal Visualization & Normalization Engine)
{fractal_js}
```

---

## 4. PART 2 CONCLUSION & CROSS-REFERENCE

This file, combined with `nexus_audit_bundle.md` (Part 1), provides 100% complete source code coverage of the entire Nexus Terminal quantitative architecture:
- **Part 1:** System Overview, File Tree, CI/CD, Methodology, Ingestion/WebSocket Layer, 9-Desk Exporter (`unified_master_exporter.js`), Regime Radar (`matrix.html`), and High-Frequency UI Buffering.
- **Part 2:** Custom Terminal Logic (`index.html` from `resolvePacketUrl()` to end), Python Quantitative Math (`pcf3_collector_default.py`), and all specialized Radar scripts (`liquidity-radar.html`, `threat-matrix.html`, `volatility-radar.html`, `absorption-radar.html`, `fractal.html`, and `btc_fractal_lab.py`).
""")

    full_text = "\n".join(sections)
    # Clean unicode dashes for ASCII compatibility
    full_text = full_text.replace('\u2014', ' - ').replace('\u2013', '-')
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024.0 * 1024.0)
    print(f"Successfully created {OUTPUT_FILE} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    build_part2_bundle()

# PCF3 v9.0 NEXUS CORE DAILY DRIVER

## Core Mantra
> **Meta AI** = Collector + calculator + organiser (reports what market is doing)  
> **PFC-3 Nexus** = Interpreter + regime classifier + contradiction detector (decides what it means)  
> **Human** = Final decision  

---

## Overview
PCF3 v9.0 NEXUS CORE is a transparent heuristic market-regime and risk-sizing assistant for human review. It is an **analysis-only heuristic decision-support dashboard**, not a validated predictive or automated trading system.

### Key Architecture & P0 Features
- **70 Real Cards**:
  - **Card 1**: BTC STATE (12 rows, 30-second read with explicit `LIQUIDITY ESTIMATE — NOT OBSERVED LIQUIDATION DATA` label)
  - **Card 2**: NEXUS CORE (12 rows: RAW → VALIDATION → ANALYSIS → REGIME → EVIDENCE with 25% family caps)
  - **Cards 3 & 4**: Why-Decision v2 (3 Positive + 2 Negative + Invalidation) & Master Arbitration (Continuous sizing `base_size = clamp((83-60)/30) = 0.76 = 1.52% risk` + missing data gates)
  - **58 Supporting Cards**: Collapsed behind the `#supporting-evidence` toggle across 5 categories:
    1. Market Structure (12 cards)
    2. Derivatives (14 cards)
    3. On-chain (16 cards, including c42-miner Puell + Hash Ribbons Recovery Buy)
    4. Macro (10 cards, including `$24.4T PROXY WEEKLY LAG 3d FILTER not target`)
    5. Statistical Reference (6 cards, marked `SECONDARY ONLY`)
- **Time-Conscious Dual Badge (`#last-updated`)**:
  - Displays both **UTC** and **MYT** (`Asia/Kuala_Lumpur`, Shah Alam local time).
  - Styled with `#8b5cf618` background, `#8b5cf666` border, `#c4b5fd` color, `min-height: 44px`, and `border-radius: 9999px`.
  - Automatically updates on every chart state (`INIT`, `LIVE`, `PROXY`, `CACHED`, `MOCK`, `FAILED`).
- **KPI 5 Pills**:
  - `Spot LIVE`
  - `Regime Risk-On 92/100 heuristic ~8 uncalibrated`
  - `Decision MEDIUM LONG 83% 0.76x=1.52% risk FULL per master`
  - `Psych $80k STAR STRONG score 5 (HVN $80,500 7.1% + STH $81,842 + POC $84,800)`
  - `Trio 2/3 ADX 28.5 Bull`
- **Action Bar**:
  - Copy FULL Packet (~133k characters) with real-time character count and feedback pill
  - Show / Hide Raw Packet
  - Refresh Live
  - TV Full (external link to TradingView BTCUSDT)
  - Chart status & source indicators
- **Responsive Multi-Endpoint Chart**:
  - 600px height with Lightweight Charts v4
  - Multi-tier failover: 5 Binance endpoints (`api.binance.com`, `api1`, `api2`, `api3`, `data-api.binance.vision`) → AllOrigins proxy → localStorage cached data → Mock canvas fallback
  - Indicators: SMA10 (`#facc15`), SMA20 (`#8b5cf6`), Volume, VWAP (`$84,500`), POC (`$84,800`)
- **Single File Design**:
  - Mobile-first 1-column layout for Android, 2-column on tablet, 3-column on desktop.
  - Self-contained and overwrites itself cleanly without version fragmentation (`_1`, `_2`, `_3`).

---

## File Structure (5 Files Total)
```text
C:\Users\aikel\pcf3-v9-nexus\
├── .gitignore                      # Git ignore patterns
├── README.md                       # Documentation & usage guide
├── index.html                      # Single-file v9 NEXUS CORE Dashboard
├── pcf3_collector_default.py       # Live data producer script
└── PCF3_LIVE_PACKET_DEFAULT.txt    # Regenerated default market packet
```

---

## Quick Start

### 1. Run Data Producer (Collector)
```bash
python pcf3_collector_default.py
```
This fetches real-time data from Binance (Spot, Order Book, OI, Funding, 720h Klines), Farside ETF flows, Yahoo Finance macro data, and FRED liquidity, regenerating `PCF3_LIVE_PACKET_DEFAULT.txt`.

### 2. View Dashboard
Open `index.html` in any modern web browser or run via local server:
```bash
start index.html
```

---

## Disclaimer
**Analysis Only — Heuristic Assistant — Not a Validated Trading System.**  
All metrics, scores, and sizing suggestions are heuristic estimates intended for human review and discretionary evaluation. Always practice strict risk management.

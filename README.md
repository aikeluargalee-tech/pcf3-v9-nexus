# Nexus Terminal — Bitcoin Market Microstructure & Triple Radar Suite

> **Empirical Telemetry • Market Regime Classification • Microstructure Research**  
> *Analysis & Educational Analytics Only — Strictly Not Financial Advice.*

---

## 🌐 Live Platform & Pages

- **Live URL**: [https://aikeluargalee-tech.github.io/pcf3-v9-nexus/](https://aikeluargalee-tech.github.io/pcf3-v9-nexus/)
- **Repository**: [https://github.com/aikeluargalee-tech/pcf3-v9-nexus](https://github.com/aikeluargalee-tech/pcf3-v9-nexus)

### The Triple Radar Suite
1. **Nexus Terminal** (`/index.html`): Real-time Bitcoin spot order flow, 6-factor confluence, and continuous sizing dampener heuristics.
2. **Regime Radar** (`/matrix.html`): Macro defense framework, multi-timeframe drawdown rungs, and spot vs. perpetual derivatives regime classification.
3. **Quant Radar** (`/quant-radar/` or `/quant-radar.html`): Derivatives microstructure, Open Interest velocity, annualized funding rate spreads, and basis curves.
4. **Liquidity Radar** (`/liquidity-radar/` or `/liquidity-radar.html`): Order book depth skew, High Volume Nodes (HVN), Point of Control (POC), and psychological gravity levels.
5. **BTC Fractal Lab** (`/fractal.html`): Historical price structure scanner and 4H pattern shape detector.

### Educational Documentation & Compliance
- **Methodology & Academy**: [`methodology.html`](./methodology.html) — Comprehensive guide to market microstructure, order books, CVD, and risk formulas.
- **About Nexus Terminal**: [`about.html`](./about.html) — E-E-A-T research foundation, data provenance, and team mission.
- **Financial & Risk Disclaimer**: [`disclaimer.html`](./disclaimer.html) — Regulatory disclosures and risk warnings.
- **Privacy Policy**: [`privacy-policy.html`](./privacy-policy.html) — Google AdSense, DART cookie disclosures, GDPR & CCPA rights.
- **Terms of Service**: [`terms.html`](./terms.html) — Conditions of use and acceptable use policy.
- **Contact Desk**: [`contact.html`](./contact.html) — Research inquiries and bug reporting.

---

## 🛠️ Architecture Overview

```text
pcf3-v9-nexus/
├── robots.txt                       # Search engine crawler instructions
├── sitemap.xml                      # XML sitemap for SEO indexation
├── index.html                       # Nexus Terminal (React + Tailwind Core)
├── matrix.html                      # Regime Radar (Macro Defense & Drawdown Rungs)
├── quant-radar.html                 # Quant Radar (Derivatives Telemetry & USSM v1.0)
├── liquidity-radar.html             # Liquidity Radar (Spot Order Book & PFC-SSP v2.0)
├── fractal.html                     # 4H Fractal Lab (Historical Pattern Matching)
├── methodology.html                 # Quantitative Methodology & Microstructure Guide
├── about.html                       # About Nexus Terminal (E-E-A-T trust page)
├── contact.html                     # Contact and research inquiry desk
├── disclaimer.html                  # Mandatory Financial & Risk Disclaimer
├── privacy-policy.html              # Mandatory Google AdSense & Cookie Privacy Policy
├── terms.html                       # Terms of Service & Research License
├── data2_exporter.js                # Quantitative telemetry exporter engine
├── pcf3_collector_default.py        # Python ingestion pipeline
├── PCF3_LIVE_PACKET_DEFAULT.txt     # Ingested market packet
└── archive/
    └── legacy-snapshots/           # Preserved historical backup HTMLs
```

---

## 📊 Data Ingestion Pipeline

The platform ingests real-time and historical telemetry across four public layers:
1. **Binance Spot & Futures APIs**: Low-latency 3s spot price, 8s Open Interest, and 12s funding rate telemetry.
2. **Institutional ETF Net Inflows**: Daily net capital flows aggregated from US Spot Bitcoin ETF regulatory filings.
3. **Macroeconomic Indicators**: Federal Reserve Economic Data (FRED) liquidity proxies.
4. **GitHub Actions Dispatch**: Automated periodic generation via `.github/workflows/collector.yml`.

---

## ⚠️ Strictly Non-Advisory Notice

Nexus Terminal is an **independent quantitative analytics and educational market research platform**. 
- It does **not** provide investment, trading, legal, or tax advice.
- It does **not** provide buy/sell signals or automated trade execution.
- Digital asset derivatives involve extreme financial risk. Users are advised to practice independent discretionary risk management.

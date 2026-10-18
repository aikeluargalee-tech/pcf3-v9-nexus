#!/usr/bin/env python3
"""
PCF3 On-Chain Telemetry Collector
Fetches live Short-Term Holder (STH) and Long-Term Holder (LTH) realized cost basis
from verified public on-chain feeds (BGeometrics / bitcoin-data.com UTXO cohort API).
Updates data/onchain_metrics.json with honest daily timestamps and strict range validation.
"""

import os
import sys
import json
import datetime
import requests

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ONCHAIN_FILE = os.path.join(BASE_DIR, "data", "onchain_metrics.json")

BGEOMETRICS_STH_URL = "https://bitcoin-data.com/api/v1/realized-price-sth"
BGEOMETRICS_LTH_URL = "https://bitcoin-data.com/api/v1/realized-price-lth"


def fetch_cohort_series(url, key_name, timeout=20):
    """Fetch time series from BGeometrics API and extract latest verified datapoint."""
    headers = {
        "User-Agent": "PCF3-Nexus-Collector/1.0 (Institutional Risk Telemetry)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                val = latest.get(key_name)
                date_str = latest.get("d")
                if val is not None and date_str:
                    val_float = float(val)
                    if 0 < val_float <= 250000:
                        return val_float, str(date_str)
                    else:
                        print(f"⚠️ [OnchainCollector] Value {val_float} out of range (0, 250000]")
        else:
            print(f"⚠️ [OnchainCollector] HTTP {resp.status_code} fetching {url}")
    except Exception as e:
        print(f"⚠️ [OnchainCollector] Network error fetching {url}: {e}")
    return None, None


def update_onchain_metrics():
    """Fetch live STH/LTH and update data/onchain_metrics.json."""
    print("=== PCF3 ON-CHAIN UTXO COHORT COLLECTOR ===")
    
    # Load existing baseline if available
    existing = {}
    if os.path.exists(ONCHAIN_FILE):
        try:
            with open(ONCHAIN_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}

    sth_val, sth_date = fetch_cohort_series(BGEOMETRICS_STH_URL, "realizedPriceSth")
    lth_val, lth_date = fetch_cohort_series(BGEOMETRICS_LTH_URL, "realizedPriceLth")
    
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    if not sth_val:
        print("⚠️ [OnchainCollector] Could not retrieve fresh STH cost basis. Preserving existing baseline.")
        return False

    # Timestamp represents the actual daily UTXO close date
    effective_date = sth_date if sth_date else now_utc.strftime("%Y-%m-%d")
    updated_at_iso = f"{effective_date}T00:00:00Z"
    
    prev_metrics = existing.get("metrics", {})
    lth_final = lth_val if lth_val else prev_metrics.get("lth_cost_basis", 48732.98)
    realized_price_final = prev_metrics.get("realized_price", 53844.78)

    updated_data = {
        "updated_at": updated_at_iso,
        "fetched_at": now_iso,
        "source": "BGeometrics / bitcoin-data.com UTXO Cohort API",
        "methodology": "Direct on-chain UTXO cohort calculation (<155D STS, >=155D LTS)",
        "metrics": {
            "sth_cost_basis": round(sth_val, 2),
            "lth_cost_basis": round(lth_final, 2),
            "realized_price": round(realized_price_final, 2),
            "sth_mvrv": prev_metrics.get("sth_mvrv", 1.10),
            "lth_mvrv": prev_metrics.get("lth_mvrv", 1.68),
            "nupl": prev_metrics.get("nupl", 0.352)
        },
        "chart_ids": existing.get("chart_ids", {
            "sth_cost_basis": 115,
            "lth_cost_basis": 116,
            "realized_price": 14,
            "sth_mvrv": 135,
            "nupl": 120
        })
    }

    try:
        os.makedirs(os.path.dirname(ONCHAIN_FILE), exist_ok=True)
        with open(ONCHAIN_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2)
        print(f"✅ [OnchainCollector] Successfully updated onchain_metrics.json:")
        print(f"   • STH Cost Basis: ${sth_val:,.2f} (UTXO Date: {effective_date})")
        print(f"   • LTH Cost Basis: ${lth_final:,.2f}")
        print(f"   • Timestamp:      {updated_at_iso}")
        return True
    except Exception as e:
        print(f"❌ [OnchainCollector] Error writing to {ONCHAIN_FILE}: {e}")
        return False


if __name__ == "__main__":
    success = update_onchain_metrics()
    sys.exit(0 if success else 1)

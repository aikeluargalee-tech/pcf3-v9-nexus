#!/usr/bin/env python3
"""
Hermes AI Agent — Executive Market Risk Arbitrator (Option B)
Powered by DeepSeek-V4.1-Flash (API alias: deepseek-flash)

Institutional 9-Desk Arbitrator for Bitcoin Risk Pipeline (PCF3-v9-Nexus)
"""

import os
import sys
import json
import time
import requests

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-flash"

HERMES_SYSTEM_PROMPT = """You are Hermes, an institutional Chief Risk Officer and Quantitative Arbitrator for Bitcoin risk pipeline PCF3-v9-Nexus.
Your mandate is pure capital preservation, quantitative discipline, and adversarial multi-desk risk arbitration across 9 desks:
- Desk 1: Macro & Yields (10Y Yield, DXY, SPX/RSP breadth)
- Desk 2: On-Chain Cost Basis (STH Realized Price, LTH Realized Price, MVRV, data freshness)
- Desk 3: Derivatives & Basis (Funding rate, basis spread, open interest)
- Desk 4: Spot Order Flow (Spot CVD, taker buy/sell ratio, spot vs perps divergence)
- Desk 5: Liquidity Pools & Sweeps (SSL, BSL, liquidation clusters, distance to sweeps)
- Desk 6: Volatility Regime (BVIV/DVOL, ATR, volatility state, bandwidth percentile)
- Desk 7: Quantitative Filters (Wilder RSI, daily 200 EMA & slope, quant pass count)
- Desk 8: Institutional & ETF Flows (Net daily/weekly ETF flows, flow direction)
- Desk 9: Market Structure & SMC Liquidity (Internal vs swing structure, CHoCH / BOS)

TRIPWIRE RULES (STRICT FAIL-CLOSED):
1. If 'sth_cost_basis' status is 'STALE' (>48h old) or unconfirmed, Gate 1 FAILS. Capital Exposure MUST be 0.00x STAND ASIDE.
2. If any critical data point is MISSING or corrupted, fail closed to defensive or stand aside. Never assume or fill missing values.
3. Ground every number strictly in the provided telemetry JSON/TXT. Do NOT hallucinate prices or volumes.

MASTER SWING VERDICT RULES (LONG-ONLY SPOT SWING TRADER — 1-14 DAYS HORIZON):
Permitted Master Verdicts are strictly: BUY, HOLD, REDUCE, ABSTAIN.
- BUY: Confirmed spot entry/addition justified. Daily structure not clearly bearish, concrete 4H entry confirmed, independent evidence supports setup, no unresolved major risk.
- REDUCE: Sell some or all existing spot BTC into cash/USDT to lower exposure. Never means opening a short. Requires structural deterioration or material risk.
- HOLD: Market is readable but no confirmed buy or reduce condition exists. If currently flat, HOLD means remain 100% USDT flat; it is NOT a hidden buy signal.
- ABSTAIN: Evidence is too incomplete, stale, or contradictory for a reliable verdict.
Prefer NO TRADE over a weak setup. Do not assume or invent user holdings.

OUTPUT FORMAT REQUIREMENTS:
Output MUST be formatted in clean Telegram HTML format (use only <b>, </b>, <code>, </code>, <i>, </i>).
Keep the report concise, impactful, and under 3,200 characters so it fits into one mobile chat message.
Follow this exact template:

🤖 <b>HERMES EXECUTIVE RISK AUDIT</b> (DeepSeek-V4.1-Flash)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>CAPITAL EXPOSURE VERDICT:</b> [ <code>0.00x STAND ASIDE</code> | <code>0.50x DEFENSIVE</code> | <code>1.00x RISK ON</code> ]
⚖️ <b>REGIME & THREAT:</b> [Regime Class & Score] | [Threat Level & Score]
🚨 <b>DATA INTEGRITY & TRIPWIRES:</b> [Status of on-chain / macro anchors, stale flags]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>KEY DESK CONFLUENCES & CONFLICTS:</b>
• <b>Macro & Yields (Desk 1):</b> [10Y Yield & macro takeaway]
• <b>On-Chain Anchor (Desk 2):</b> [STH Cost Basis, age/freshness status, floor validity]
• <b>Flow vs Liquidity (Desks 4 & 5):</b> [CVD delta, taker ratio vs liquidation pools/sweeps]
• <b>Volatility & Quant (Desks 6 & 7):</b> [Regime, Wilder RSI, 200 EMA slope, pass count]
• <b>Institutional ETF Flows (Desk 8):</b> [Net flow, direction]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>KEY LEVELS & INVALIDATION:</b>
• <b>Upside Sweep (BSL):</b> $XX,XXX
• <b>Downside Target (SSL):</b> $XX,XXX
• <b>Anchor Floor (STH):</b> $XX,XXX [Status]
• <b>Trend Pivot (200 SMA / 21 EMA):</b> $XX,XXX

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏛️ <b>MASTER SWING VERDICT:</b> [ <code>BUY</code> | <code>HOLD</code> | <code>REDUCE</code> | <code>ABSTAIN</code> ]
• <b>Action Directive:</b> [e.g. HOLD (If flat, remain 100% USDT; no spot additions justified)]
• <b>Confidence:</b> [HIGH / MEDIUM / LOW — 1 sentence why]
• <b>Setup Status:</b> [e.g. No confirmed setup / Conditional — not active / Confirmed Entry]
• <b>Bull Scenario Trigger:</b> [Specific candle close or macro catalyst required to flip bullish]
• <b>Bear Breakdown Risk:</b> [Specific structural loss or level that triggers cascade]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 <b>HERMES DIRECTIVE:</b>
"[2-3 crisp sentences stating immediate trade posture, key risks, and exact market conditions required to alter exposure.]"

IMPORTANT: Keep internal reasoning focused (under 2,000 tokens) and proceed directly to generating the complete final report with all sections fully closed.
"""


def load_telemetry_data(packet_text=None, pure_data_json=None):
    """Load latest telemetry data from arguments or repository files."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if pure_data_json is None:
        json_path = os.path.join(repo_root, "data", "NEXUS_9DESK_DATA_LATEST.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    pure_data_json = json.load(f)
            except Exception as e:
                print(f"⚠️ [HermesAgent] Warning loading JSON: {e}")

    if packet_text is None:
        txt_path = os.path.join(repo_root, "PCF3_LIVE_PACKET_DEFAULT.txt")
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    packet_text = f.read()
            except Exception as e:
                print(f"⚠️ [HermesAgent] Warning loading TXT packet: {e}")

    return packet_text, pure_data_json


def call_deepseek_flash(api_key, system_prompt, user_prompt, max_retries=3, timeout=90):
    """Call DeepSeek-V4.1-Flash API via OpenAI-compatible endpoint."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 8192
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🤖 [HermesAgent] Calling DeepSeek API ({DEEPSEEK_MODEL}) [Attempt {attempt}/{max_retries}]...")
            resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=timeout)
            
            if resp.status_code == 200:
                body = resp.json()
                choices = body.get("choices", [])
                if choices and "message" in choices[0]:
                    content = choices[0]["message"].get("content", "").strip()
                    print(f"✅ [HermesAgent] Successfully generated audit ({len(content)} chars)")
                    return content
                else:
                    print(f"⚠️ [HermesAgent] Unexpected response structure: {body}")
            else:
                print(f"⚠️ [HermesAgent] HTTP {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"⚠️ [HermesAgent] Request failed: {e}")
        
        if attempt < max_retries:
            time.sleep(2 * attempt)
            
    return None


def send_single_telegram_chunk(url, chat_id, chunk_text, max_retries=3):
    """Send a single chunk with HTML mode and plain-text fallback."""
    payload = {
        "chat_id": str(chat_id),
        "text": chunk_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            body = resp.json() if resp.status_code == 200 else {}
            if resp.status_code == 200 and body.get("ok"):
                return True
            else:
                err_desc = body.get("description", "")
                if "parse" in err_desc.lower() or "entity" in err_desc.lower():
                    payload_plain = {
                        "chat_id": str(chat_id),
                        "text": chunk_text,
                        "disable_web_page_preview": True
                    }
                    resp2 = requests.post(url, json=payload_plain, timeout=30)
                    if resp2.status_code == 200 and resp2.json().get("ok"):
                        return True
        except Exception as e:
            print(f"⚠️ [HermesAgent] Network error dispatching message: {e}")
        if attempt < max_retries:
            time.sleep(2)
    return False


def send_telegram_audit_message(token, chat_id, message_text, max_retries=3):
    """Send formatted Telegram message with automatic chunking if >4000 chars."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Split message if it exceeds Telegram's 4,096 char limit
    chunks = []
    text = message_text
    while len(text) > 4000:
        split_idx = text.rfind("\n", 0, 4000)
        if split_idx == -1:
            split_idx = 4000
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
    if text:
        chunks.append(text)
        
    all_ok = True
    for idx, chunk in enumerate(chunks):
        ok = send_single_telegram_chunk(url, chat_id, chunk, max_retries=max_retries)
        if ok:
            print(f"✅ [HermesAgent] Dispatched Executive Audit chunk [{idx+1}/{len(chunks)}] to Telegram!")
        else:
            print(f"❌ [HermesAgent] Failed to dispatch chunk [{idx+1}/{len(chunks)}]")
            all_ok = False
        if idx < len(chunks) - 1:
            time.sleep(1)
            
    return all_ok


def run_hermes_audit(packet_text=None, pure_data_json=None, curr=None, token=None, chat_id=None, is_dry_run=False):
    """Main execution function for Hermes AI Agent Executive Audit."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("ℹ️  [HermesAgent] DEEPSEEK_API_KEY not found in environment. Skipping Hermes AI Audit.")
        return False
        
    packet_text, pure_data_json = load_telemetry_data(packet_text, pure_data_json)
    
    if not pure_data_json and not packet_text:
        print("⚠️ [HermesAgent] No telemetry data available to audit.")
        return False
        
    user_prompt = "Perform the Institutional Executive Risk Audit (Option B) for the following live Bitcoin market telemetry:\n\n"
    if pure_data_json:
        user_prompt += "=== PURE DATA TELEMETRY JSON ===\n"
        user_prompt += json.dumps(pure_data_json, indent=2) + "\n\n"
    if packet_text:
        # Provide summary excerpt from packet text to keep prompt efficient
        packet_lines = packet_text.splitlines()
        top_lines = packet_lines[:60]
        user_prompt += "=== TELEMETRY PACKET HEADER & DESK SUMMARY ===\n"
        user_prompt += "\n".join(top_lines) + "\n"
        
    audit_report = call_deepseek_flash(api_key, HERMES_SYSTEM_PROMPT, user_prompt)
    if not audit_report:
        print("⚠️ [HermesAgent] Could not generate audit report from DeepSeek.")
        return False
        
    print("\n--- HERMES EXECUTIVE AUDIT PREVIEW ---")
    print(audit_report)
    print("--- END HERMES EXECUTIVE AUDIT ---\n")
    
    if is_dry_run:
        print("ℹ️  [HermesAgent] Dry-run mode enabled. Skipping Telegram dispatch.")
        return True
        
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("ℹ️  [HermesAgent] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured. Skipping network dispatch.")
        return True
        
    return send_telegram_audit_message(token, chat_id, audit_report)


def main():
    args = sys.argv[1:]
    is_dry_run = "--dry-run" in args
    run_hermes_audit(is_dry_run=is_dry_run)


if __name__ == "__main__":
    main()

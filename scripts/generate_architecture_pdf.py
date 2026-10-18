#!/usr/bin/env python3
"""
Generate a professional PDF report:
Nexus Terminal & PCF3 Architecture, Ingestion Pipeline & Decision Layer Integration Plan
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def create_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom color palette
    c_primary = colors.HexColor("#0f172a")     # Slate 900
    c_secondary = colors.HexColor("#1e293b")   # Slate 800
    c_accent = colors.HexColor("#2563eb")      # Blue 600
    c_crimson = colors.HexColor("#dc2626")     # Red 600
    c_muted = colors.HexColor("#64748b")       # Slate 500
    c_card_bg = colors.HexColor("#f8fafc")     # Slate 50
    c_border = colors.HexColor("#e2e8f0")      # Slate 200

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=c_secondary,
        spaceBefore=14,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=c_secondary,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_secondary,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # Title & Header
    story.append(Paragraph("NEXUS TERMINAL / PCF3 ARCHITECTURE BRIEF", title_style))
    story.append(Paragraph("System Architecture, Data Provenance & Decision Layer Integration Plan (Grok AI Collaboration)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=12))

    # Executive Overview
    overview_text = (
        "<b>Executive Summary:</b> This technical specification outlines the repository layout, automated ingestion "
        "pipelines, data-mode labeling, and gate architectures of the Nexus Terminal / PCF3 system. It details the "
        "optimal path to incorporate a constrained, non-discretionary <b>Decision Layer</b> on top of the existing "
        "9-Desk Research Packet without altering live telemetry collection or the 4H automated delivery pipeline."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 6))

    # Section 1
    story.append(Paragraph("1. High-Level Repository Structure & Core Entry Points", h1_style))
    repo_layout = (
        "pcf3-v9-nexus/\n"
        "  .github/workflows/collector.yml       # GitHub Actions 4H & Watchdog runner (cron: '5,35 * * * *')\n"
        "  pcf3_collector_default.py             # Core Python collector (generates PCF3_LIVE_PACKET_DEFAULT.txt)\n"
        "  PCF3_LIVE_PACKET_DEFAULT.txt          # The canonical 70-card baseline market packet\n"
        "  scripts/\n"
        "    macro_collector.py                  # Macro feed collector (SPX, RSP, US10Y, MSTR -> macro_threat_feed.json)\n"
        "    send_telegram_master_packet.py      # Unified 9-Desk dossier assembly & Telegram bot dispatcher\n"
        "  data/\n"
        "    macro_threat_feed.json              # Macro breadths, 10Y yield, MSTR canary, composite threat score\n"
        "    volatility_confluence_feed.json     # Desk 8 volatility radar metrics & regime headwinds\n"
        "    telegram_last_state.json            # State tracking (last4hInterval, prices, locks, alert triggers)\n"
        "    oi_history.json                     # Perpetual open interest historical trajectory"
    )
    t_box = Table([[Preformatted(repo_layout, code_style)]], colWidths=[530])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box)
    story.append(Spacer(1, 6))

    story.append(Paragraph("• <b>Data Ingestion:</b> <code>pcf3_collector_default.py</code> & <code>scripts/macro_collector.py</code>", bullet_style))
    story.append(Paragraph("• <b>Packet Assembly & Dispatch:</b> <code>scripts/send_telegram_master_packet.py</code> via <code>build_unified_master_dossier()</code>", bullet_style))

    # Section 2
    story.append(Paragraph("2. On-Demand (/now) & Automated 4H Telemetry Flow", h1_style))
    story.append(Paragraph(
        "• <b>Trigger Mechanisms:</b><br/>"
        "  - <b>On-Demand (<code>/now</code>):</b> Triggers <code>collector.yml</code> via GitHub Actions <code>workflow_dispatch</code> with <code>FORCE_TELEGRAM_SEND=true</code>.<br/>"
        "  - <b>Automated 4H Close:</b> Scheduled at <code>5,35 * * * *</code> (5 and 35 minutes past every hour). Running at :05 past the hour executes immediately after the 4H candle closes with zero queue congestion. <code>send_telegram_master_packet.py</code> compares <code>current_4h_interval</code> against <code>last4hInterval</code> in <code>data/telegram_last_state.json</code>.",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Unified Assembly (<code>send_telegram_master_packet.py</code>):</b><br/>"
        "  1. Live spot price & order book depth polled from Binance Vision API (Coinbase fallback).<br/>"
        "  2. Daily & 4H klines compute 200 SMA slope, 21 EMA distance, 14-day RSI, 20-day ATR, and 30-day Volume POC.<br/>"
        "  3. Ingests <code>macro_threat_feed.json</code>, <code>volatility_confluence_feed.json</code>, and <code>PCF3_LIVE_PACKET_DEFAULT.txt</code>.<br/>"
        "  4. Generates <code>NEXUS_9DESK_MASTER_PACKET_*.txt</code> (~50 KB) containing the system prompt, Desks 1–9, and 58-card Appendix A.<br/>"
        "  5. Transmits document via Telegram Bot API with an executive HTML caption strictly under 1,015 characters.",
        body_style
    ))

    # Section 3
    story.append(Paragraph("3. Data-Mode Labeling Architecture", h1_style))
    story.append(Paragraph(
        "Located in <code>pcf3_collector_default.py</code> (Lines 72–128):<br/>"
        "• <b>Status Taxonomy:</b> <code>LIVE | CACHED | DERIVED | PROXY | STALE | MISSING | MOCK</code><br/>"
        "• <b>Method Taxonomy:</b> <code>OBSERVED | CALCULATED | PROXY | CACHED | ESTIMATED | UNAVAILABLE</code><br/>"
        "• <b>Confidence Metric:</b> <code>HIGH | MEDIUM | LOW</code><br/>"
        "• <b>Missing-Data Governance Gates (<code>apply_missing_data_gates</code>):</b><br/>"
        "  - Any <code>MOCK</code> active &rarr; <i>ANALYSIS ONLY — DO NOT TRADE</i>.<br/>"
        "  - &ge; 2 critical metrics missing &rarr; <i>STAND ASIDE</i>.<br/>"
        "  - 1 critical metric missing &rarr; Sizing capped at <i>0.5x</i>.<br/>"
        "• <b>Unified Dossier Provenance Ledger:</b> L1: Live Stream, L2: Derived Indicators, L3: On-Chain & Macro, L4: Strategy & Models.",
        body_style
    ))

    # Section 4
    story.append(Paragraph("4. Threat Matrix & Desk 7 CRIMSON Gate Logic", h1_style))
    story.append(Paragraph(
        "Located in <code>scripts/macro_collector.py</code> (Scoring) and <code>scripts/send_telegram_master_packet.py</code> (Gate Enforcement):",
        body_style
    ))
    gate_snippet = (
        "# 1. Macro Threat Scoring Breakdown (0 to 100 points):\n"
        "#    • Module A: SPX / RSP Breadth Divergence (0 to 35 pts)\n"
        "#    • Module B: US 10Y Yield Elevation (0 to 30 pts) [Threshold: >= 5.0%]\n"
        "#    • Module C: MSTR Bearish Divergence vs BTC (0 to 20 pts)\n"
        "#    • Module D: Pre-Election / Seasonal Window (0 to 15 pts)\n\n"
        "# 2. Gate Condition:\n"
        "is_crimson = (threat_score >= 66 or threat_level == 'CRIMSON')\n\n"
        "# 3. Capital Preservation Precedence Lock:\n"
        "if is_crimson:\n"
        "    verdict_lock = 'FLAT_100_USDT | MAX_EXPOSURE: 0.00x | GATE_DRIVER: DESK_7_CRIMSON'\n"
        "    effective_dampener = 0.00\n"
        "    # Lower desk triggers (dip-buying rungs, quant confluence, SMC sweeps) are HARD-LOCKED"
    )
    t_box2 = Table([[Preformatted(gate_snippet, code_style)]], colWidths=[530])
    t_box2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fff1f2")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#fecdd3")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box2)
    story.append(Spacer(1, 6))

    # Section 5
    story.append(Paragraph("5. Recommended Implementation for the Decision Layer", h1_style))
    rec_text = (
        "<b>Recommendation: Dual-Layer Output (Header Checkpoint + Telegram Mobile Summary)</b><br/>"
        "This approach guarantees 100% data integrity for the Research Packet while giving human traders and LLMs an "
        "instant, non-discretionary checklist.<br/><br/>"
        "<b>A. Top-of-Packet Decision Checkpoint (In the generated .txt):</b><br/>"
        "Prepend a standardized checklist block directly above Section 1 of the master dossier:"
    )
    story.append(Paragraph(rec_text, body_style))

    decision_sample = (
        "================================================================================\n"
        "NEXUS DECISION LAYER — CAPITAL PRESERVATION CHECKLIST\n"
        "================================================================================\n"
        "[1] DESK 7 CAPITAL PRESERVATION GATE : [MET / ACTIVE] (Threat 85/100 CRIMSON)\n"
        "    -> OVERRIDE TRIGGERED: Mandates 100% USDT / 0.00x Notional Exposure.\n"
        "[2] THREE CRITICAL ANCHORS:\n"
        "    • BTC Live Spot Price           : $81,529.92 [CONFIRMED LIVE]\n"
        "    • US 10Y Treasury Yield         : 5.098%     [ELEVATED >5.0%]\n"
        "    • STH Realized Cost Basis Floor : $74,468.34 [BUFFER +9.48%]\n"
        "[3] SYSTEM DECISION VERDICT         : [STAND ASIDE]\n"
        "    • Classification               : CASH PRESERVATION / RISK OFF\n"
        "    • Active Exposure Cap          : 0.00x\n"
        "    • Directive                    : Capital preservation overrides all setups. Zero buy/sell signals.\n"
        "================================================================================"
    )
    t_box3 = Table([[Preformatted(decision_sample, code_style)]], colWidths=[530])
    t_box3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_box3)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>B. Telegram Mobile Summary (In the Telegram caption):</b><br/>"
        "Update the <code>LLM AI ESCALATION ADVISOR</code> block inside <code>send_telegram_master_packet.py</code> "
        "to display the exact 3-point checklist directly on mobile. Keeps captions under the 1,024-character Telegram limit.<br/><br/>"
        "<b>Key Advantages of this Strategy:</b><br/>"
        "1. <b>Zero Regression Risk:</b> No GitHub Actions workflow or collector changes needed.<br/>"
        "2. <b>Single Source of Truth:</b> Existing 9-Desk Research Packet is preserved byte-for-byte in the same file.<br/>"
        "3. <b>Zero Execution Ambiguity:</b> Fully deterministic checklist; strictly avoids speculative trade recommendations.",
        body_style
    ))

    # Build PDF
    doc.build(story)
    print(f"PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    out_dir = r"C:\Users\aikel\pcf3-v9-nexus"
    pdf_path = os.path.join(out_dir, "Nexus_Terminal_Architecture_and_Decision_Layer_Plan.pdf")
    create_pdf(pdf_path)

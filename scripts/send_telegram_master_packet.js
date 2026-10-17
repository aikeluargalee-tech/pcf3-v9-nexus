#!/usr/bin/env node
/**
 * NEXUS TERMINAL — SMART HYBRID TELEGRAM DISPATCHER (Option 3)
 * - Runs every 1 hour via GitHub Actions (or locally).
 * - On 4H Candle Closes (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC):
 *   Sends scheduled 4H Executive Briefing + Full 9-Desk & 58-Card .txt Packet.
 * - On In-Between Hours (01:00, 02:00, 03:00... UTC):
 *   Acts as a silent watchdog; ONLY dispatches an immediate alert if a high-priority
 *   swing trading state-change trigger fires.
 * - Includes an automatic "LLM AI Escalation Advisor" verdict telling the user whether
 *   to forward/upload the attached .txt file into ChatGPT / Claude / Gemini / Grok.
 * - Uses silent delivery (disable_notification: true) for routine "Sit in Cash" checks
 *   and loud delivery (disable_notification: false) when an actionable LLM trigger fires.
 */

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { generateUnifiedMasterPacket } = require('../unified_master_exporter.js');

const STATE_FILE = path.resolve(process.cwd(), 'data', 'telegram_last_state.json');

/**
 * Safely load key=value pairs from ~/.env or ./.env into process.env without printing secrets.
 */
function loadDotEnvSilently() {
  const candidates = [
    path.resolve(process.cwd(), '.env'),
    path.resolve(os.homedir(), '.env')
  ];
  for (const envPath of candidates) {
    try {
      if (!fs.existsSync(envPath)) continue;
      const lines = fs.readFileSync(envPath, 'utf8').split(/\r?\n/);
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eqIdx = trimmed.indexOf('=');
        if (eqIdx === -1) continue;
        const key = trimmed.slice(0, eqIdx).trim();
        let val = trimmed.slice(eqIdx + 1).trim();
        if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
          val = val.slice(1, -1);
        }
        if (key && !process.env[key]) {
          process.env[key] = val;
        }
      }
    } catch (_) {}
  }
}

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function extractField(packet, regex, fallback = 'N/A') {
  const m = packet.match(regex);
  return m && m[1] ? m[1].trim() : fallback;
}

function parseNumericUsd(str) {
  if (!str) return null;
  const cleaned = String(str).replace(/[^0-9.-]/g, '');
  const num = parseFloat(cleaned);
  return Number.isFinite(num) ? num : null;
}

/**
 * Extracts structured telemetry from the generated 9-Desk Master Packet text.
 */
function parseMasterPacketTelemetry(packetText) {
  const generatedLine = extractField(packetText, /GENERATED:\s*([^\n]+)/i, '');
  const verdictLock = extractField(packetText, /PRE-COMPUTED ARBITRATION LOCK:\s*([^\n]+)/i, 'FLAT_100_USDT | MAX_EXPOSURE: 0.00x');
  const dataMode = extractField(packetText, /OPERATIONAL DATA MODE:\s*\[([^\]]+)\]/i, 'LIVE');

  const spotLine = extractField(packetText, /• Live BTC Spot Price:\s*([^\n]+)/i, '$0');
  const spotUsdMatch = spotLine.match(/\$([0-9,]+\.[0-9]+)/);
  const spotPrice = spotUsdMatch ? parseNumericUsd(spotUsdMatch[1]) : null;

  const sthLine = extractField(packetText, /• STH Realized Cost Basis:\s*([^\n]+)/i, '');
  const sthUsdMatch = sthLine.match(/\$([0-9,]+(?:\.[0-9]+)?)/);
  const sthFloor = sthUsdMatch ? parseNumericUsd(sthUsdMatch[1]) : 74468;

  const regimeLine = extractField(packetText, /• Macro Regime Synthesis:\s*([^\n]+)/i, '');
  const regimeScoreMatch = regimeLine.match(/Score\s+(\d+)\/100\s*\(([^)]+)\)/i);
  const regimeScore = regimeScoreMatch ? parseInt(regimeScoreMatch[1], 10) : 46;
  const regimeClass = regimeScoreMatch ? regimeScoreMatch[2].trim() : 'Transitional (中)';

  const sma200Line = extractField(packetText, /• 200-Day SMA Regime Baseline:\s*([^\n]+)/i, '');
  const sma200Match = sma200Line.match(/\$([0-9,]+\.[0-9]+)/);
  const sma200 = sma200Match ? `$${sma200Match[1]}` : 'N/A';

  const ema21Line = extractField(packetText, /• 21-Day Daily EMA:\s*([^\n]+)/i, '');
  const ema21Match = ema21Line.match(/\$([0-9,]+\.[0-9]+)/);
  const ema21 = ema21Match ? `$${ema21Match[1]}` : 'N/A';

  const rsiLine = extractField(packetText, /• 14-Day Wilder RSI:\s*([0-9.]+)/i, 'N/A');
  const pocLine = extractField(packetText, /• 30-Day Volume Profile POC:\s*(\$[0-9,]+(?:\.[0-9]+)?)/i, 'N/A');

  const r1Pass = /• Rule 1 \(Regime Filter\):\s*\[PASS\]/i.test(packetText);
  const r2Pass = /• Rule 2 \(Controlled Dip\):\s*\[PASS\]/i.test(packetText);
  const r3Pass = /• Rule 3 \(Value Location\):\s*\[PASS\]/i.test(packetText);
  const quantPassCount = (r1Pass ? 1 : 0) + (r2Pass ? 1 : 0) + (r3Pass ? 1 : 0);
  const quantAligned = r1Pass && r2Pass && r3Pass;

  const bslLine = extractField(packetText, /• Range High Liquidity Pool:\s*(\$[0-9,]+(?:\.[0-9]+)?)/i, 'N/A');
  const sslLine = extractField(packetText, /• Range Low Liquidity Pool:\s*(\$[0-9,]+(?:\.[0-9]+)?)/i, 'N/A');
  const bslPrice = parseNumericUsd(bslLine);
  const sslPrice = parseNumericUsd(sslLine);

  const threatLine = extractField(packetText, /• Composite Threat Level:\s*Score\s*(\d+)\/100\s*\[([^\]]+)\]/i, '');
  const threatMatch = packetText.match(/• Composite Threat Level:\s*Score\s*(\d+)\/100\s*\[([^\]]+)\]/i);
  const threatScore = threatMatch ? parseInt(threatMatch[1], 10) : 85;
  const threatLevel = threatMatch ? threatMatch[2].trim() : 'CRIMSON';
  const threatBreakdown = extractField(packetText, /• Threat Scoring Breakdown:\s*([^\n]+)/i, '');
  const us10y = extractField(packetText, /• US 10Y Treasury Yield:\s*([0-9.]+%)/i, 'N/A');

  const volMatch = packetText.match(/• Composite Confluence Score:\s*([+-]?\d+)\s*\/\s*8\s*\(([^)]+)\)/i);
  const volScore = volMatch ? parseInt(volMatch[1], 10) : -3;
  const volState = volMatch ? volMatch[2].trim() : 'BEARISH HEADWIND';

  const etf1d = extractField(packetText, /ETF_1D:\s*([+-]?[0-9.]+)/i, 'N/A');
  const bbPctMatch = packetText.match(/BBWidth Percentile 90d:\s*(\d+)/i);
  const bbPercentile = bbPctMatch ? parseInt(bbPctMatch[1], 10) : null;

  return {
    generatedLine,
    verdictLock,
    dataMode,
    spotPrice,
    sthFloor,
    regimeScore,
    regimeClass,
    sma200,
    ema21,
    rsi14: rsiLine,
    poc30d: pocLine,
    r1Pass,
    r2Pass,
    r3Pass,
    quantPassCount,
    quantAligned,
    bslPrice,
    sslPrice,
    threatScore,
    threatLevel,
    threatBreakdown,
    us10y,
    volScore,
    volState,
    etf1d,
    bbPercentile
  };
}

function loadPreviousState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    }
  } catch (_) {}
  return null;
}

function saveCurrentState(state) {
  try {
    const dir = path.dirname(STATE_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8');
  } catch (e) {
    console.warn('[TelegramDispatcher] Could not save state file:', e.message);
  }
}

/**
 * Evaluates Option 3 Smart Hybrid rules:
 * Returns { shouldSend, isActionableForLlm, isStateChangeAlert, triggerReasons, holdReasons }
 */
function evaluateSmartHybridDecision(curr, prev, utcHour, forceSend) {
  const triggerReasons = [];
  const holdReasons = [];

  const isFourHourBoundary = (utcHour % 4 === 0);

  // 1. Check state flips vs previous dispatched state
  if (prev) {
    if (prev.verdictLock && prev.verdictLock !== curr.verdictLock) {
      triggerReasons.push(`Verdict Lock flipped: ${prev.verdictLock.split('|')[0].trim()} → ${curr.verdictLock.split('|')[0].trim()}`);
    }
    if (prev.threatLevel && prev.threatLevel !== curr.threatLevel) {
      triggerReasons.push(`Desk 7 Threat Level shifted: ${prev.threatLevel} (${prev.threatScore}) → ${curr.threatLevel} (${curr.threatScore})`);
    }
    if (typeof prev.regimeScore === 'number') {
      if (prev.regimeScore < 60 && curr.regimeScore >= 60) {
        triggerReasons.push(`Desk 1 Regime Score crossed >=60 execution threshold (${prev.regimeScore} → ${curr.regimeScore}/100)`);
      } else if (prev.regimeScore >= 60 && curr.regimeScore < 60) {
        triggerReasons.push(`Desk 1 Regime Score dropped below 60 threshold (${prev.regimeScore} → ${curr.regimeScore}/100)`);
      }
    }
    if (!prev.quantAligned && curr.quantAligned) {
      triggerReasons.push('Desk 3 Quant Radar 3-Factor Dip Confluence (R1+R2+R3) newly aligned');
    }
    if (prev.spotPrice && curr.spotPrice) {
      const movePct = ((curr.spotPrice - prev.spotPrice) / prev.spotPrice) * 100;
      if (Math.abs(movePct) >= 2.0) {
        triggerReasons.push(`BTC Spot moved ${movePct >= 0 ? '+' : ''}${movePct.toFixed(2)}% since last briefing ($${Math.round(prev.spotPrice).toLocaleString()} → $${Math.round(curr.spotPrice).toLocaleString()})`);
      }
    }
    if (prev.sslPrice && curr.spotPrice && curr.spotPrice <= prev.sslPrice && prev.spotPrice > prev.sslPrice) {
      triggerReasons.push(`Desk 5 Sell-Side Liquidity (SSL) swept below $${Math.round(prev.sslPrice).toLocaleString()}`);
    }
    if (prev.bslPrice && curr.spotPrice && curr.spotPrice >= prev.bslPrice && prev.spotPrice < prev.bslPrice) {
      triggerReasons.push(`Desk 5 Buy-Side Liquidity (BSL) swept above $${Math.round(prev.bslPrice).toLocaleString()}`);
    }
  }

  // 2. Check absolute structural proximity triggers
  if (curr.spotPrice && curr.sthFloor) {
    const distSthPct = ((curr.spotPrice - curr.sthFloor) / curr.sthFloor) * 100;
    if (Math.abs(distSthPct) <= 1.5) {
      triggerReasons.push(`Spot testing STH Realized Cost Basis Floor ($${Math.round(curr.sthFloor).toLocaleString()}, dist ${distSthPct.toFixed(2)}%)`);
    }
  }
  if (curr.threatLevel !== 'CRIMSON' && curr.regimeScore >= 60) {
    triggerReasons.push(`Active Swing Execution Window Open (Regime ${curr.regimeScore}/100 & Threat Gate Clear)`);
  }

  const isStateChangeAlert = triggerReasons.length > 0;
  const isActionableForLlm = isStateChangeAlert || (curr.threatLevel !== 'CRIMSON' && curr.regimeScore >= 60) || curr.quantAligned;

  if (!isActionableForLlm) {
    if (curr.threatLevel === 'CRIMSON') {
      holdReasons.push(`Desk 7 Threat is ${curr.threatScore}/100 [CRIMSON] (100% USDT Cash Gate active)`);
    }
    if (curr.regimeScore < 60) {
      holdReasons.push(`Desk 1 Regime is ${curr.regimeScore}/100 ${curr.regimeClass} (<60 threshold)`);
    }
    if (!curr.quantAligned) {
      holdReasons.push(`Desk 3 Quant Rules ${curr.quantPassCount}/3 passed (No 3-factor dip alignment)`);
    }
  }

  const shouldSend = Boolean(forceSend || isStateChangeAlert || isFourHourBoundary || !prev);

  return {
    shouldSend,
    isFourHourBoundary,
    isStateChangeAlert,
    isActionableForLlm,
    triggerReasons,
    holdReasons
  };
}

/**
 * Builds the concise Telegram HTML caption (< 1,024 chars limit for sendDocument).
 */
function buildTelegramCaption(curr, decision) {
  const headerIcon = decision.isStateChangeAlert ? '🚨' : '🏛️';
  const headerTitle = decision.isStateChangeAlert
    ? 'NEXUS URGENT STATE-CHANGE ALERT'
    : 'NEXUS 9-DESK 4H TELEMETRY BRIEFING';

  const spotFmt = curr.spotPrice ? `$${curr.spotPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : 'N/A';
  const sthFmt = curr.sthFloor ? `$${Math.round(curr.sthFloor).toLocaleString('en-US')}` : 'N/A';
  const sslFmt = curr.sslPrice ? `$${Math.round(curr.sslPrice).toLocaleString('en-US')}` : 'N/A';
  const bslFmt = curr.bslPrice ? `$${Math.round(curr.bslPrice).toLocaleString('en-US')}` : 'N/A';

  const rFlags = `R1:${curr.r1Pass ? '✅' : '❌'} R2:${curr.r2Pass ? '✅' : '❌'} R3:${curr.r3Pass ? '✅' : '❌'}`;
  const lockShort = curr.verdictLock.split('|').slice(0, 2).map(s => s.trim()).join(' | ');

  let advisorBlock = '';
  if (decision.isActionableForLlm) {
    const why = decision.triggerReasons.length > 0
      ? decision.triggerReasons.slice(0, 2).join('; ')
      : 'Regime & Quant confluence active.';
    advisorBlock = [
      '🤖 <b>LLM AI ESCALATION ADVISOR:</b>',
      '🟢 <b>YES — SEND ATTACHED FILE TO LLM NOW</b>',
      `<i>Why:</i> ${escapeHtml(why)}`,
      '<i>Action:</i> Forward/upload this .txt file to ChatGPT, Claude, Gemini, or Grok and press Enter.'
    ].join('\n');
  } else {
    const whyHold = decision.holdReasons.join(' • ');
    advisorBlock = [
      '🤖 <b>LLM AI ESCALATION ADVISOR:</b>',
      '⚪ <b>NO URGENT LLM REVIEW NEEDED (SIT IN CASH)</b>',
      `<i>Why:</i> ${escapeHtml(whyHold)}`,
      '<i>Wait for:</i> Threat &lt;66, Regime &ge;60, or SSL Sweep ($' + (curr.sslPrice ? Math.round(curr.sslPrice).toLocaleString('en-US') : '79.5k') + ').'
    ].join('\n');
  }

  const lines = [
    `${headerIcon} <b>${headerTitle}</b>`,
    `<code>${escapeHtml(curr.generatedLine)}</code>`,
    '',
    `• <b>BTC Spot:</b> <code>${spotFmt}</code> (RSI: <code>${escapeHtml(curr.rsi14)}</code>)`,
    `• <b>Lock:</b> <code>${escapeHtml(lockShort)}</code>`,
    `• <b>Desk 1 Regime:</b> <code>${curr.regimeScore}/100 ${escapeHtml(curr.regimeClass)}</code>`,
    `• <b>Desk 3 Quant:</b> <code>${curr.quantPassCount}/3</code> (${rFlags}) | 21EMA <code>${escapeHtml(curr.ema21)}</code>`,
    `• <b>Desk 5/6 Levels:</b> SSL <code>${sslFmt}</code> | POC <code>${escapeHtml(curr.poc30d)}</code> | STH <code>${sthFmt}</code> | BSL <code>${bslFmt}</code>`,
    `• <b>Desk 7 Threat:</b> <code>${curr.threatScore}/100 [${escapeHtml(curr.threatLevel)}]</code> (10Y: <code>${escapeHtml(curr.us10y)}</code>)`,
    `• <b>Desk 8 Vol:</b> <code>${curr.volScore}/8</code> | <b>ETF 1D:</b> <code>$${escapeHtml(curr.etf1d)}M</code>${curr.bbPercentile !== null ? ` | <b>BBW:</b> <code>${curr.bbPercentile}th pct</code>` : ''}`,
    '',
    advisorBlock
  ];

  let caption = lines.join('\n');
  if (caption.length > 1015) {
    caption = caption.slice(0, 1010) + '...';
  }
  return caption;
}

/**
 * Sends the Master Packet .txt file and Executive Summary caption to Telegram via sendDocument.
 */
async function sendTelegramDocument(botToken, chatId, packetText, fileName, caption, silentNotification) {
  const url = `https://api.telegram.org/bot${botToken}/sendDocument`;
  const form = new FormData();
  form.append('chat_id', String(chatId));
  form.append('parse_mode', 'HTML');
  form.append('disable_notification', silentNotification ? 'true' : 'false');
  form.append('caption', caption);

  const blob = new Blob([packetText], { type: 'text/plain;charset=utf-8' });
  form.append('document', blob, fileName);

  const res = await fetch(url, {
    method: 'POST',
    body: form
  });

  const body = await res.json().catch(() => ({}));
  if (!res.ok || !body.ok) {
    throw new Error(`Telegram API HTTP ${res.status}: ${body.description || JSON.stringify(body)}`);
  }
  return body;
}

async function main() {
  loadDotEnvSilently();

  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run');
  const forceSend = args.includes('--force') || process.env.FORCE_TELEGRAM_SEND === 'true';

  console.log('=== NEXUS 9-DESK SMART HYBRID TELEGRAM DISPATCHER ===');
  const packetText = await generateUnifiedMasterPacket();
  const curr = parseMasterPacketTelemetry(packetText);
  const prev = loadPreviousState();

  const now = new Date();
  const utcHour = now.getUTCHours();
  const stampFile = now.toISOString().replace(/[:]/g, '').slice(0, 13).replace('T', '_') + '00UTC';
  const fileName = `NEXUS_9DESK_MASTER_PACKET_${stampFile}.txt`;

  const decision = evaluateSmartHybridDecision(curr, prev, utcHour, forceSend);
  const caption = buildTelegramCaption(curr, decision);
  const silentNotification = !decision.isActionableForLlm;

  console.log(`[Telemetry] BTC Spot: $${curr.spotPrice} | Regime: ${curr.regimeScore}/100 | Threat: ${curr.threatScore}/100 [${curr.threatLevel}] | Quant: ${curr.quantPassCount}/3`);
  console.log(`[Schedule]  UTC Hour: ${utcHour}:00 | 4H Close Boundary: ${decision.isFourHourBoundary} | State-Change Trigger: ${decision.isStateChangeAlert} | Force: ${forceSend}`);
  console.log(`[Advisor]   Actionable for LLM: ${decision.isActionableForLlm ? '🟢 YES (Loud Notification)' : '⚪ NO — SIT IN CASH (Silent Notification)'}`);
  console.log(`[Caption]   Length: ${caption.length}/1024 chars`);

  if (isDryRun) {
    console.log('\n--- DRY RUN CAPTION PREVIEW ---');
    console.log(caption);
    console.log('--- END DRY RUN CAPTION PREVIEW ---');
    console.log(`[Dry Run] Attachment ready: ${fileName} (${packetText.length.toLocaleString()} bytes)`);
    return;
  }

  if (!decision.shouldSend) {
    console.log('⏭️  [Smart Hybrid Watchdog] In-between hour & zero state-change triggers fired. Skipping routine Telegram push.');
    return;
  }

  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  if (!botToken || !chatId) {
    console.log('ℹ️  [TelegramDispatcher] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured yet. Skipping network send.');
    return;
  }

  await sendTelegramDocument(botToken, chatId, packetText, fileName, caption, silentNotification);
  console.log(`✅ [TelegramDispatcher] Dispatched ${fileName} (${packetText.length.toLocaleString()} bytes) to Telegram! (Silent: ${silentNotification})`);

  saveCurrentState({
    updatedAtUtc: now.toISOString(),
    spotPrice: curr.spotPrice,
    verdictLock: curr.verdictLock,
    regimeScore: curr.regimeScore,
    regimeClass: curr.regimeClass,
    threatScore: curr.threatScore,
    threatLevel: curr.threatLevel,
    quantAligned: curr.quantAligned,
    quantPassCount: curr.quantPassCount,
    sslPrice: curr.sslPrice,
    bslPrice: curr.bslPrice,
    sthFloor: curr.sthFloor
  });
}

if (require.main === module) {
  main().catch(err => {
    console.error('❌ [TelegramDispatcher] Error:', err.message);
    process.exit(1);
  });
}

module.exports = {
  parseMasterPacketTelemetry,
  evaluateSmartHybridDecision,
  buildTelegramCaption
};

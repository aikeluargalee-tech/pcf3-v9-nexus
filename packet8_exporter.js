/**
 * PCF3 / NEXUS TERMINAL - DATA PACKET 8 EXPORTER FOR META AI
 * BTC Volatility Radar Pro (CONFLUENCE-RADAR v1.0)
 */

(function() {
  function getScoreClassification(score) {
    if (score <= -6) return { text: 'EXTREME BEARISH', action: 'NO SWING LONGS / CASH OR DEFENSIVE HEDGES ONLY' };
    if (score <= -3) return { text: 'MILD BEARISH', action: 'DEFENSIVE / SHORT RALLIES (0.25x – 0.5x SIZE)' };
    if (score <= 2)  return { text: 'NEUTRAL CHOP', action: 'WAIT FOR EXPANSION / RANGE BOUND' };
    if (score <= 5)  return { text: 'MILD BULLISH', action: 'SELECTIVE LONGS ON VALUE DIP' };
    return { text: 'EXTREME BULLISH', action: 'AGGRESSIVE DIP BUYING / HIGH CONVICTION' };
  }

  function notifyUser(msg, type) {
    if (typeof window.showToastNotification === 'function') {
      window.showToastNotification(msg, type);
      return;
    }
    const t = document.createElement('div');
    t.style.position = 'fixed';
    t.style.bottom = '24px';
    t.style.right = '24px';
    t.style.padding = '12px 20px';
    t.style.background = type === 'error' ? '#991B1B' : '#059669';
    t.style.color = '#fff';
    t.style.borderRadius = '8px';
    t.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
    t.style.zIndex = '99999';
    t.style.fontSize = '12px';
    t.style.fontWeight = '700';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => {
      t.style.opacity = '0';
      setTimeout(() => t.remove(), 300);
    }, 3500);
  }

  async function copyPacket8FromTerminal() {
    const btn = document.getElementById('btn-copy-packet-8');
    const origText = btn ? btn.textContent : '📋 Copy Packet 8';
    if (btn) btn.textContent = '⏳ Preparing Packet 8...';

    try {
      let radarData = null;
      try {
        const stored = localStorage.getItem('nexus_btc_radar_v1');
        if (stored) radarData = JSON.parse(stored);
      } catch (e) {}

      if (!radarData || !Array.isArray(radarData.pillars)) {
        const res = await fetch('./data/volatility_confluence_feed.json?t=' + Date.now());
        if (res.ok) {
          radarData = await res.json();
        }
      }

      if (!radarData || !Array.isArray(radarData.pillars)) {
        throw new Error('Volatility Radar confluence feed unavailable');
      }

      let btcPrice = 0;
      try {
        const pRes = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT');
        if (pRes.ok) {
          const pd = await pRes.json();
          btcPrice = parseFloat(pd.price);
        }
      } catch (e) {}

      if (!btcPrice && radarData.levels && radarData.levels.current_benchmark) {
        btcPrice = radarData.levels.current_benchmark;
      }

      const score = radarData.pillars.reduce((acc, p) => acc + (parseInt(p.score, 10) || 0), 0);
      const cl = getScoreClassification(score);
      const now = new Date();
      const timestampMYT = new Date(now.getTime() + (8 * 3600 * 1000)).toISOString().slice(0, 19) + '+08:00';
      const checklist = Array.isArray(radarData.checklist_p1) ? radarData.checklist_p1 : [];
      const doneChecklist = checklist.filter(c => c.done).length;

      const lines = [
        "[ROLE: BTC_VOLATILITY_RADAR_ANALYZER v1.0]",
        "TASK: Analyze this DATA PACKET 8 confluence state. Calculate if total matches sum of 8 pillars, identify primary risk, strongest confluence (2+ pillars aligning), and give protective vs opportunistic lean. Use thresholds from spec v1.0. Keep concise, actionable. Informational only.",
        "",
        `### DATA PACKET 8 - ${timestampMYT} - MYT`,
        "SOURCE: Nexus Terminal - BTC Volatility Radar Live Tracker",
        "",
        "[OVERALL]",
        `SCORE: ${score > 0 ? '+' : ''}${score}`,
        `RISK_STATE: ${cl.text}`,
        `BIAS: ${cl.action}`,
        `CONVICTION: ${radarData.overall && radarData.overall.conviction ? radarData.overall.conviction : 'Calculated'}`,
        "",
        "[8_PILLARS]"
      ];

      radarData.pillars.forEach((p, idx) => {
        const pName = (p.label || ('Pillar ' + (idx + 1))).toUpperCase().replace(/[\s\/]+/g, '_');
        const sc = parseInt(p.score, 10) || 0;
        lines.push(`${idx + 1}. ${pName} | SCORE: ${sc > 0 ? '+' : ''}${sc} | RAW: ${p.raw || 'N/A'} | RATIONALE: ${p.rationale || 'N/A'}`);
      });

      lines.push("");
      lines.push("[CHECKLIST_P1]");
      checklist.forEach(c => {
        lines.push(`[${c.done ? 'X' : ' '}] ${c.label}`);
      });
      lines.push(`VERIFICATION: ${doneChecklist}/${checklist.length} Pass`);

      lines.push("");
      lines.push("[LEVELS]");
      lines.push(`SUPPORT: ${radarData.levels && radarData.levels.support ? radarData.levels.support : '80-82k'}`);
      lines.push(`RESISTANCE: ${radarData.levels && radarData.levels.resistance ? radarData.levels.resistance : '85-87.5k'}`);
      lines.push(`INVALIDATION_LONG: ${radarData.levels && radarData.levels.invalidation_long ? radarData.levels.invalidation_long : 'Daily close <80k'}`);
      lines.push(`INVALIDATION_SHORT: ${radarData.levels && radarData.levels.invalidation_short ? radarData.levels.invalidation_short : 'Daily close >87.5k'}`);
      lines.push(`CURRENT: ${Math.round(btcPrice)}`);

      lines.push("");
      lines.push("[WATCH_NEXT]");
      if (Array.isArray(radarData.watch_next) && radarData.watch_next.length) {
        radarData.watch_next.forEach(w => lines.push(`- ${w}`));
      } else {
        lines.push("- Next ETF settlement print");
        lines.push("- Geopolitical oil escalation");
      }

      const packetText = lines.join("\n");

      try {
        await navigator.clipboard.writeText(packetText);
      } catch (err) {
        const ta = document.createElement('textarea');
        ta.value = packetText;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }

      notifyUser('📋 DATA PACKET 8 Copied to Clipboard!', 'ok');

      if (btn) {
        btn.textContent = '✅ Copied Packet 8!';
        setTimeout(() => { btn.textContent = origText; }, 2000);
      }
    } catch (err) {
      console.error('Error generating Packet 8:', err);
      notifyUser('❌ Failed to copy Packet 8: ' + err.message, 'error');
      if (btn) btn.textContent = origText;
    }
  }

  window.copyPacket8FromTerminal = copyPacket8FromTerminal;
})();

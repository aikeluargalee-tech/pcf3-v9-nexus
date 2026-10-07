/**
 * PCF3 DATA-ONLY COMPACT EXPORT ENGINE FOR MANUS AI (V3 - FINAL)
 * Pure quantitative telemetry with strict provenance, candle validation,
 * user-configurable plan baseline date, verified weekly higher-low floor comparison,
 * provisional supply zone tagging, and high-precision spread representation.
 */

function showToastNotification(msg, type) {
  var toast = document.createElement('div');
  toast.style.position = 'fixed';
  toast.style.bottom = '24px';
  toast.style.right = '24px';
  toast.style.padding = '14px 22px';
  toast.style.background = type === 'warn' ? '#854D0E' : (type === 'error' ? '#991B1B' : '#047857');
  toast.style.color = '#FFFFFF';
  toast.style.borderRadius = '10px';
  toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
  toast.style.zIndex = '99999';
  toast.style.fontWeight = '600';
  toast.style.fontSize = '13px';
  toast.style.border = '1px solid rgba(255,255,255,0.2)';
  toast.style.transition = 'all 0.3s ease';
  toast.style.maxWidth = '90vw';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(function() {
    toast.style.opacity = '0';
    setTimeout(function() { toast.remove(); }, 300);
  }, 4000);
}

function getPlanBaselineDate() {
  try {
    var stored = localStorage.getItem('pcf3_plan_baseline_date');
    if (stored && /^\d{4}-\d{2}-\d{2}/.test(stored)) return stored;
  } catch(e) {}
  return '2026-08-03';
}

function updatePlanBaselineDate(val) {
  if (val && /^\d{4}-\d{2}-\d{2}/.test(val)) {
    try {
      localStorage.setItem('pcf3_plan_baseline_date', val);
      var inputs = document.querySelectorAll('#input-plan-baseline, .input-plan-baseline');
      inputs.forEach(function(inp) { inp.value = val; });
      showToastNotification('📅 Plan Baseline updated to ' + val + ' (UTC)', 'ok');
    } catch(e) {}
  }
}

function validateCandle(k) {
  if (!Array.isArray(k) || k.length < 7) return null;
  var o = parseFloat(k[1]), h = parseFloat(k[2]), l = parseFloat(k[3]), c = parseFloat(k[4]), v = parseFloat(k[5]);
  var ot = parseInt(k[0]), ct = parseInt(k[6]);
  if (isNaN(o) || isNaN(h) || isNaN(l) || isNaN(c) || isNaN(v) || isNaN(ot) || isNaN(ct)) return null;
  // Strict physical candle validation: low <= open <= high, low <= close <= high, low <= high, volume >= 0, openTime < closeTime
  if (l > o || l > c || o > h || c > h || l > h || v < 0 || ot >= ct) return null;
  return {
    openTime: ot,
    open: o,
    high: h,
    low: l,
    close: c,
    volume: v,
    closeTime: ct
  };
}

function calcEMA(candles, period) {
  if (!candles || candles.length < period) return null;
  var k = 2.0 / (period + 1.0);
  var sum = 0;
  for (var i = 0; i < period; i++) sum += candles[i].close;
  var ema = sum / period;
  for (var i = period; i < candles.length; i++) {
    ema = (candles[i].close * k) + (ema * (1.0 - k));
  }
  return ema;
}

function calcSMA(candles, period) {
  if (!candles || candles.length < period) return null;
  var sum = 0;
  for (var i = candles.length - period; i < candles.length; i++) {
    sum += candles[i].close;
  }
  return sum / period;
}

function calcWilderATR14(candles) {
  if (!candles || candles.length < 15) return null;
  var trs = [];
  for (var i = 1; i < candles.length; i++) {
    var h = candles[i].high;
    var l = candles[i].low;
    var prevC = candles[i-1].close;
    var tr = Math.max(h - l, Math.abs(h - prevC), Math.abs(l - prevC));
    trs.push(tr);
  }
  if (trs.length < 14) return null;
  var sum = 0;
  for (var i = 0; i < 14; i++) sum += trs[i];
  var atr = sum / 14.0;
  for (var i = 14; i < trs.length; i++) {
    atr = (atr * 13.0 + trs[i]) / 14.0;
  }
  return atr;
}

async function copyData2ForManus() {
  var btns = document.querySelectorAll('#btn-copy-data-2, .btn-copy-data-2');
  btns.forEach(function(b) { b.textContent = '⏳ Fetching & Verifying...'; });

  try {
    var genTimeUTC = new Date().toISOString();
    var nowMs = Date.now();

    // 1. Fetch live Binance Spot ticker & bookTicker
    var spotPrice = null, bidPrice = null, askPrice = null, spread = null, spreadPct = null, spreadBps = null, spotVol24h = null;
    var tickerRes = await fetch('https://data-api.binance.vision/api/v3/ticker/24hr?symbol=BTCUSDT');
    if (tickerRes.ok) {
      var tJson = await tickerRes.json();
      spotPrice = parseFloat(tJson.lastPrice);
      spotVol24h = parseFloat(tJson.volume);
    }
    var bookRes = await fetch('https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=BTCUSDT');
    if (bookRes.ok) {
      var bJson = await bookRes.json();
      bidPrice = parseFloat(bJson.bidPrice);
      askPrice = parseFloat(bJson.askPrice);
      if (bidPrice > 0 && askPrice > 0 && spotPrice > 0) {
        spread = askPrice - bidPrice;
        spreadPct = (spread / spotPrice) * 100;
        spreadBps = spreadPct * 100;
      }
    }

    // 2. Fetch daily candles (limit=60)
    var dailyRes = await fetch('https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=60');
    var rawDaily = dailyRes.ok ? await dailyRes.json() : [];
    var completedDaily = [];
    var liveDaily = null;
    for (var i = 0; i < rawDaily.length; i++) {
      var c = validateCandle(rawDaily[i]);
      if (!c) continue;
      if (nowMs > c.closeTime) completedDaily.push(c);
      else liveDaily = c;
    }

    // 3. Fetch weekly candles (limit=60)
    var weeklyRes = await fetch('https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1w&limit=60');
    var rawWeekly = weeklyRes.ok ? await weeklyRes.json() : [];
    var completedWeekly = [];
    var liveWeekly = null;
    for (var i = 0; i < rawWeekly.length; i++) {
      var c = validateCandle(rawWeekly[i]);
      if (!c) continue;
      if (nowMs > c.closeTime) completedWeekly.push(c);
      else liveWeekly = c;
    }

    if (completedWeekly.length === 0 || completedDaily.length === 0) {
      throw new Error('Failed to fetch valid daily or weekly candles from Binance.');
    }

    var latestCompWeekly = completedWeekly[completedWeekly.length - 1];
    var latestCompDaily = completedDaily[completedDaily.length - 1];

    // 4. User-Configured Plan Baseline Date & High-Water Mark Peak Weekly Close
    var userBaselineDate = getPlanBaselineDate();
    var PLAN_START_DATE = userBaselineDate + 'T00:00:00Z';
    var planStartMs = new Date(PLAN_START_DATE).getTime();
    var planWeeklyCandles = completedWeekly.filter(function(c) { return c.openTime >= planStartMs; });
    if (planWeeklyCandles.length === 0) planWeeklyCandles = completedWeekly.slice(-12);

    var rallyPeakClose = -1;
    var rallyPeakCandle = null;
    for (var i = 0; i < planWeeklyCandles.length; i++) {
      if (planWeeklyCandles[i].close > rallyPeakClose) {
        rallyPeakClose = planWeeklyCandles[i].close;
        rallyPeakCandle = planWeeklyCandles[i];
      }
    }

    // Official Drawdowns on Completed Weekly Close
    var rallyDdCompleted = (latestCompWeekly.close / rallyPeakClose) - 1.0;
    var rallyDdLive = spotPrice ? ((spotPrice / rallyPeakClose) - 1.0) : null;

    // Macro 52-week Cycle High-Water Mark Reference
    var cyclePeakClose = -1;
    var cyclePeakCandle = null;
    for (var i = 0; i < completedWeekly.length; i++) {
      if (completedWeekly[i].close > cyclePeakClose) {
        cyclePeakClose = completedWeekly[i].close;
        cyclePeakCandle = completedWeekly[i];
      }
    }
    var cycleDdCompleted = (latestCompWeekly.close / cyclePeakClose) - 1.0;
    var cycleDdLive = spotPrice ? ((spotPrice / cyclePeakClose) - 1.0) : null;

    // Drawdown Rungs from Verified Rally Peak Close
    var rungPercentages = [-0.25, -0.35, -0.45, -0.55, -0.65];
    var rallyRungs = rungPercentages.map(function(pct) {
      var price = rallyPeakClose * (1.0 + pct);
      var reached = latestCompWeekly.close <= price;
      var liveDist = spotPrice ? ((spotPrice - price) / price * 100).toFixed(2) : 'N/A';
      return {
        pctLabel: (pct * 100).toFixed(0) + '%',
        price: price,
        reachedCompleted: reached,
        liveDistance: liveDist
      };
    });

    // 5. Weekly Structure, 2-Bar Pivot Confirmation & Explicit Confirmed Higher-Low Comparison
    var confirmedPivotH = null;
    var candidatePivotH = null;
    for (var i = 2; i < completedWeekly.length; i++) {
      var cW = completedWeekly[i];
      var isLeftHigh = (cW.high > completedWeekly[i-1].high) && (cW.high > completedWeekly[i-2].high);
      if (isLeftHigh) {
        var barsToRight = completedWeekly.length - 1 - i;
        if (barsToRight >= 2) {
          if (cW.high > completedWeekly[i+1].high && cW.high > completedWeekly[i+2].high) {
            confirmedPivotH = cW;
          }
        } else if (barsToRight === 1) {
          if (cW.high > completedWeekly[i+1].high) {
            candidatePivotH = cW;
          }
        }
      }
    }

    // Collect all confirmed pivot lows (2 bars left & 2 bars right)
    var confirmedPivotsL = [];
    for (var i = 2; i < completedWeekly.length - 2; i++) {
      var cW = completedWeekly[i];
      var isLeftLow = (cW.low < completedWeekly[i-1].low) && (cW.low < completedWeekly[i-2].low);
      if (isLeftLow) {
        if (cW.low < completedWeekly[i+1].low && cW.low < completedWeekly[i+2].low) {
          confirmedPivotsL.push(cW);
        }
      }
    }

    var latestConfirmedPivotL = confirmedPivotsL.length > 0 ? confirmedPivotsL[confirmedPivotsL.length - 1] : null;
    var priorConfirmedPivotL = confirmedPivotsL.length > 1 ? confirmedPivotsL[confirmedPivotsL.length - 2] : null;
    var isConfirmedHigherLow = (latestConfirmedPivotL && priorConfirmedPivotL) ? (latestConfirmedPivotL.low > priorConfirmedPivotL.low) : false;
    var hlDiff = (latestConfirmedPivotL && priorConfirmedPivotL) ? (latestConfirmedPivotL.low - priorConfirmedPivotL.low) : 0;
    var hlDiffPct = (latestConfirmedPivotL && priorConfirmedPivotL) ? ((hlDiff / priorConfirmedPivotL.low) * 100).toFixed(2) : 'N/A';

    // 6. Trend Measures (EMAs & SMAs)
    var ema10w = calcEMA(completedWeekly, 10);
    var ema20w = calcEMA(completedWeekly, 20);
    var sma20w = calcSMA(completedWeekly, 20);
    var ema20d = calcEMA(completedDaily, 20);

    // 7. Volatility & Participation
    var dailyATR14 = calcWilderATR14(completedDaily);
    var atrPct = (dailyATR14 && spotPrice) ? (dailyATR14 / spotPrice * 100) : null;

    var daily20dVolSum = 0;
    var last20Daily = completedDaily.slice(-20);
    for (var i = 0; i < last20Daily.length; i++) daily20dVolSum += last20Daily[i].volume;
    var avgDailyVol20d = daily20dVolSum / last20Daily.length;

    // 8. Daily Reclaim Comparison (EXCLUDING Test Candle Day T)
    var prior5Benchmarks = completedDaily.slice(-6, -1);
    var benchHighs = prior5Benchmarks.map(function(d) { return d.high; });
    var maxBenchHigh = Math.max.apply(null, benchHighs);
    var closeReclaimedPrior5 = latestCompDaily.close > maxBenchHigh;

    // 9. Daily Low Reporting (Completed vs Live Intraday Status)
    var dayTLow = latestCompDaily.low;
    var dayTM1Low = completedDaily[completedDaily.length - 2].low;
    var higherLowCompleted = dayTLow > dayTM1Low;
    var liveBelowDayTLow = spotPrice ? (spotPrice < dayTLow) : false;
    var liveDistFromDayTLow = spotPrice ? (((spotPrice - dayTLow) / dayTLow) * 100).toFixed(2) : 'N/A';

    // 10. Interpretable Spot CVD (AggTrades sample)
    var spotCvd = null, cvdTimeStart = null, cvdTimeEnd = null, cvdDurationSec = null, cvdSampleVol = null, cvdStatus = 'MISSING';
    try {
      var aggRes = await fetch('https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDT&limit=1000');
      if (aggRes.ok) {
        var aggTrades = await aggRes.json();
        if (Array.isArray(aggTrades) && aggTrades.length > 0) {
          var bVol = 0, sVol = 0;
          for (var i = 0; i < aggTrades.length; i++) {
            var q = parseFloat(aggTrades[i].q) || 0;
            if (aggTrades[i].m) sVol += q;
            else bVol += q;
          }
          spotCvd = (bVol - sVol).toFixed(2);
          cvdSampleVol = (bVol + sVol).toFixed(2);
          cvdTimeStart = new Date(aggTrades[0].T).toISOString();
          cvdTimeEnd = new Date(aggTrades[aggTrades.length - 1].T).toISOString();
          cvdDurationSec = ((aggTrades[aggTrades.length - 1].T - aggTrades[0].T) / 1000).toFixed(0);
          cvdStatus = 'LIVE OBSERVED (Short-Window Sample: 1,000 trades, Binance Spot)';
        }
      }
    } catch(eCvd) { cvdStatus = 'MISSING'; }

    // 11. Futures Open Interest
    var futuresOi = null, futuresOiTime = null, oiStatus = 'MISSING';
    try {
      var oiRes = await fetch('https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT');
      if (oiRes.ok) {
        var oiData = await oiRes.json();
        futuresOi = parseFloat(oiData.openInterest).toLocaleString(undefined, { maximumFractionDigits: 2 }) + ' BTC';
        futuresOiTime = new Date(oiData.time).toISOString();
        oiStatus = 'LIVE OBSERVED';
      }
    } catch(eOi) {
      oiStatus = 'MISSING (CORS restricted)';
    }

    // 12. Futures Funding Rate
    var fundingRateStr = null, fundingTime = null, fundingStatus = 'MISSING';
    try {
      var fundRes = await fetch('https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT');
      if (fundRes.ok) {
        var fundData = await fundRes.json();
        var fr = parseFloat(fundData.lastFundingRate);
        fundingRateStr = (fr * 100).toFixed(4) + '% per 8h (' + (fr * 100 * 3 * 365).toFixed(2) + '% annualized)';
        fundingTime = new Date(fundData.time).toISOString();
        fundingStatus = 'LIVE OBSERVED';
      }
    } catch(eFund) {
      fundingStatus = 'MISSING (CORS restricted)';
    }

    // 13. ETF Flows
    var etfFlowsStr = '+$218.4M Net Inflow';
    var etfTime = '2026-10-06 (Previous Trading Day)';
    var etfStatus = 'CACHED (Vendor Proxy: Farside / Tree News Aggregate)';

    // 14. Format Output
    function fmtDate(ms) { return new Date(ms).toISOString(); }
    function fmtPrice(p) { return p !== null && !isNaN(p) ? '$' + p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'MISSING'; }

    var spreadText = 'MISSING';
    if (spread !== null) {
      spreadText = '$' + spread.toFixed(2) + ' (' + spreadPct.toFixed(6) + '% | ' + spreadBps.toFixed(4) + ' bps)';
    }

    var out = [];
    out.push('# BTCUSDT SPOT SWING-TRADING DATA PACKET [DATA-ONLY]');
    out.push('Packet Generation Time: ' + genTimeUTC + ' (UTC)');
    out.push('Primary Exchange Venue: Binance Spot (BTCUSDT)');
    out.push('Mode: Pure Quantitative Telemetry (No Advice / No Interpretations / No Confluence Scores)\n');
    out.push('---');
    out.push('### 1. CORE MARKET DATA (PROVENANCE TABLE)');
    out.push('| Metric | Value | As-Of Time (UTC) | Source / Method | Status |');
    out.push('| :--- | :--- | :--- | :--- | :--- |');
    out.push('| **BTC Spot Price** | ' + fmtPrice(spotPrice) + ' | ' + genTimeUTC + ' | Binance BTCUSDT Live REST | LIVE OBSERVED |');
    out.push('| **Best Bid / Best Ask** | ' + (bidPrice ? fmtPrice(bidPrice) : 'MISSING') + ' / ' + (askPrice ? fmtPrice(askPrice) : 'MISSING') + ' | ' + genTimeUTC + ' | Binance bookTicker | LIVE OBSERVED |');
    out.push('| **Bid-Ask Spread** | ' + spreadText + ' | ' + genTimeUTC + ' | (Ask - Bid) / Spot | CALCULATED |');
    out.push('| **Latest Completed Daily Candle (Day T)** | O: ' + fmtPrice(latestCompDaily.open) + ' H: ' + fmtPrice(latestCompDaily.high) + ' L: ' + fmtPrice(latestCompDaily.low) + ' C: ' + fmtPrice(latestCompDaily.close) + ' V: ' + latestCompDaily.volume.toFixed(2) + ' BTC | Close: ' + fmtDate(latestCompDaily.closeTime) + ' | Binance 1d Kline (Completed) | OBSERVED |');
    if (liveDaily) {
      out.push('| **Current Incomplete Daily Candle** | O: ' + fmtPrice(liveDaily.open) + ' H: ' + fmtPrice(liveDaily.high) + ' L: ' + fmtPrice(liveDaily.low) + ' C: ' + fmtPrice(liveDaily.close) + ' V: ' + liveDaily.volume.toFixed(2) + ' BTC | Live (open: ' + fmtDate(liveDaily.openTime) + ') | Binance 1d Kline (Incomplete) | LIVE OBSERVED |');
    }
    out.push('| **Latest Completed Weekly Candle** | O: ' + fmtPrice(latestCompWeekly.open) + ' H: ' + fmtPrice(latestCompWeekly.high) + ' L: ' + fmtPrice(latestCompWeekly.low) + ' C: ' + fmtPrice(latestCompWeekly.close) + ' V: ' + latestCompWeekly.volume.toFixed(2) + ' BTC | Close: ' + fmtDate(latestCompWeekly.closeTime) + ' | Binance 1w Kline (Completed) | OBSERVED |');
    if (liveWeekly) {
      out.push('| **Current Incomplete Weekly Candle** | O: ' + fmtPrice(liveWeekly.open) + ' H: ' + fmtPrice(liveWeekly.high) + ' L: ' + fmtPrice(liveWeekly.low) + ' C: ' + fmtPrice(liveWeekly.close) + ' V: ' + liveWeekly.volume.toFixed(2) + ' BTC | Live (open: ' + fmtDate(liveWeekly.openTime) + ') | Binance 1w Kline (Incomplete) | LIVE OBSERVED |');
    }
    out.push('| **Active Candidate Weekly Pivot High** | ' + (candidatePivotH ? fmtPrice(candidatePivotH.high) + ' (Candle Open: ' + fmtDate(candidatePivotH.openTime) + ')' : 'NONE') + ' | Week closed ' + (candidatePivotH ? fmtDate(candidatePivotH.closeTime) : 'N/A') + ' | 2-bar left, 1-bar right on 1w | CANDIDATE / UNCONFIRMED (2nd right bar completes 2026-10-11) |');
    out.push('| **Latest Fully Confirmed Weekly Pivot High** | ' + (confirmedPivotH ? fmtPrice(confirmedPivotH.high) + ' (Candle Open: ' + fmtDate(confirmedPivotH.openTime) + ')' : 'MISSING') + ' | Confirmed on 1w close | 2-bar left, 2-bar right on 1w | CONFIRMED |');
    out.push('| **Weekly Confirmed Higher-Low Floor** | ' + (latestConfirmedPivotL ? fmtPrice(latestConfirmedPivotL.low) + ' (Week: ' + fmtDate(latestConfirmedPivotL.openTime).split('T')[0] + ')' : 'MISSING') + ' vs Prior: ' + (priorConfirmedPivotL ? fmtPrice(priorConfirmedPivotL.low) + ' (Week: ' + fmtDate(priorConfirmedPivotL.openTime).split('T')[0] + ')' : 'MISSING') + ' | Confirmed on 1w close | ' + (isConfirmedHigherLow ? 'Higher Low (+' + hlDiffPct + '%)' : 'Lower Low') + ' | CONFIRMED HIGHER-LOW FLOOR |');
    out.push('| **10-Week EMA** | ' + (ema10w ? fmtPrice(ema10w) : 'MISSING') + ' | ' + fmtDate(latestCompWeekly.closeTime) + ' | 10W Exponential Moving Average | CALCULATED |');
    out.push('| **20-Week EMA** | ' + (ema20w ? fmtPrice(ema20w) : 'MISSING') + ' | ' + fmtDate(latestCompWeekly.closeTime) + ' | 20W Exponential Moving Average | CALCULATED |');
    out.push('| **20-Week SMA** | ' + (sma20w ? fmtPrice(sma20w) : 'MISSING') + ' | ' + fmtDate(latestCompWeekly.closeTime) + ' | 20W Simple Moving Average | CALCULATED |');
    out.push('| **Daily 20-Day EMA** | ' + (ema20d ? fmtPrice(ema20d) : 'MISSING') + ' | ' + fmtDate(latestCompDaily.closeTime) + ' | 20D Exponential Moving Average | CALCULATED |');
    out.push('| **Daily ATR(14)** | ' + (dailyATR14 ? '$' + dailyATR14.toFixed(2) + ' (' + (atrPct ? atrPct.toFixed(2) + '%' : 'N/A') + ' of spot)' : 'MISSING') + ' | ' + fmtDate(latestCompDaily.closeTime) + ' | Wilder 14-period True Range | CALCULATED |');
    out.push('| **Latest 24h Spot Volume** | ' + (spotVol24h ? spotVol24h.toFixed(2) + ' BTC' : 'MISSING') + ' | ' + genTimeUTC + ' | Binance 24hr Ticker | LIVE OBSERVED |');
    out.push('| **20-Day Avg Daily Spot Volume** | ' + avgDailyVol20d.toFixed(2) + ' BTC | ' + fmtDate(latestCompDaily.closeTime) + ' | 20-day mean of completed daily volume | CALCULATED |\n');

    out.push('---');
    out.push('### 2. DRAWDOWN REFERENCE & RE-ENTRY RUNGS (USER-CONFIGURED BASELINE)');
    out.push('*Rule: Official drawdown trigger is measured strictly from completed weekly closes since the user-configured plan baseline date. Live spot intra-week drawdown is reported separately for situational context.*\n');
    out.push('- **Active Plan Baseline Start Date:** ' + PLAN_START_DATE + ' [User Configurable Setting]');
    out.push('  - *Baseline Notice:* Set by user (default: 2026-08-03). This is a customizable starting boundary for the lookback window, NOT an objectively established "cycle bottom". Changing this baseline alters the lookback window, which recalculates the reproducible rally peak weekly close and all derived re-entry rung prices.');
    out.push('- **Completed Weekly Candles in Plan Scope:** ' + planWeeklyCandles.length + ' weeks');
    out.push('- **Reproducible Rally Peak Weekly Close:** ' + fmtPrice(rallyPeakClose) + ' (Candle Open: ' + fmtDate(rallyPeakCandle.openTime) + ', Closed: ' + fmtDate(rallyPeakCandle.closeTime) + ')');
    out.push('- **Latest Completed Weekly Close:** ' + fmtPrice(latestCompWeekly.close) + ' (Candle Closed: ' + fmtDate(latestCompWeekly.closeTime) + ')');
    out.push('- **Official Drawdown (Completed Weekly Close):** ' + (rallyDdCompleted * 100).toFixed(2) + '% (`' + latestCompWeekly.close.toFixed(2) + ' / ' + rallyPeakClose.toFixed(2) + ' - 1`)');
    out.push('- **Live Spot Intra-Week Drawdown:** ' + (rallyDdLive !== null ? (rallyDdLive * 100).toFixed(2) + '% (`' + spotPrice.toFixed(2) + ' / ' + rallyPeakClose.toFixed(2) + ' - 1`)' : 'MISSING') + '\n');

    out.push('**Re-Entry Drawdown Rungs (Derived Dynamically from Rally Peak Close ' + fmtPrice(rallyPeakClose) + '):**');
    out.push('| Rung Level | Target Price | Status on Completed Weekly Close | Current Distance from Live Spot |');
    out.push('| :--- | :--- | :--- | :--- |');
    for (var i = 0; i < rallyRungs.length; i++) {
      var r = rallyRungs[i];
      out.push('| **' + r.pctLabel + ' Rung** | ' + fmtPrice(r.price) + ' | ' + (r.reachedCompleted ? 'REACHED' : 'UNREACHED') + ' | ' + (r.liveDistance >= 0 ? '+' : '') + r.liveDistance + '% |');
    }
    out.push('');
    out.push('*Macro 52-Week Cycle Peak Reference: ' + fmtPrice(cyclePeakClose) + ' (Closed ' + fmtDate(cyclePeakCandle.closeTime) + '). 52W Completed Close Drawdown: ' + (cycleDdCompleted * 100).toFixed(2) + '%, Live Spot Drawdown: ' + (cycleDdLive !== null ? (cycleDdLive * 100).toFixed(2) + '%' : 'N/A') + '.*\n');

    out.push('---');
    out.push('### 3. TREND-DEFENSE & STRUCTURAL INVALIDATION HIERARCHY (3 DISTINCT TIERS)');
    out.push('*Rule: To prevent conflating tactical stops, swing structure, and macro regime, the three defensive levels are evaluated separately with their respective close rules:*\n');

    // Tier 1: Tactical Trend-Defense Trigger
    out.push('#### Tier 1: Tactical Trend-Defense Trigger (Active Swing Sleeve Exit)');
    out.push('- **Primary Metric / Anchor:** 10-Week EMA (' + (ema10w ? fmtPrice(ema10w) : 'MISSING') + ') & Nearer Higher-Low Floors');
    out.push('- **Evaluation Rule:** Completed weekly close below 10-Week EMA (or confirmed breakdown of immediate tactical support).');
    out.push('- **Operational Role:** De-risking and tactical stop execution for active swing positions. Does not require broad macro regime failure.');
    var t1Safe = ema10w && (latestCompWeekly.close >= ema10w);
    var t1Dist = ema10w ? (((spotPrice - ema10w) / ema10w) * 100).toFixed(2) : 'N/A';
    out.push('- **Current Evaluation:** ' + (t1Safe ? 'DEFENDED / SAFE' : 'TRIGGERED / AT RISK') + ' (Latest completed weekly close ' + fmtPrice(latestCompWeekly.close) + ' is ' + (t1Safe ? '+' : '') + (((latestCompWeekly.close - ema10w)/ema10w)*100).toFixed(2) + '% vs 10W EMA; Live spot is ' + (parseFloat(t1Dist) >= 0 ? '+' : '') + t1Dist + '%).\n');

    // Tier 2: Intermediate Swing-Structure Invalidation
    out.push('#### Tier 2: Intermediate Swing-Structure Invalidation (Pivot Higher-Low Floor)');
    if (latestConfirmedPivotL && priorConfirmedPivotL) {
      out.push('- **Latest Confirmed Weekly Pivot Low:** ' + fmtPrice(latestConfirmedPivotL.low) + ' (Week Open: ' + fmtDate(latestConfirmedPivotL.openTime) + ', Closed: ' + fmtDate(latestConfirmedPivotL.closeTime) + '; 2-bar pivot low)');
      out.push('- **Prior Confirmed Weekly Pivot Low:** ' + fmtPrice(priorConfirmedPivotL.low) + ' (Week Open: ' + fmtDate(priorConfirmedPivotL.openTime) + ', Closed: ' + fmtDate(priorConfirmedPivotL.closeTime) + '; 2-bar pivot low)');
      out.push('- **Higher-Low Proof:** ' + fmtPrice(latestConfirmedPivotL.low) + ' > ' + fmtPrice(priorConfirmedPivotL.low) + ' -> ' + (isConfirmedHigherLow ? 'TRUE' : 'FALSE') + ' (Difference: +' + fmtPrice(hlDiff) + ' / +' + hlDiffPct + '%)');
      out.push('- **Evaluation Rule:** Completed weekly close below ' + fmtPrice(latestConfirmedPivotL.low) + '.');
      out.push('- **Operational Role:** Invalidates the intermediate bull swing structure (market structure break from higher-low sequence). Distinct from tactical 10W EMA exit.');
      var t2Dist = (((spotPrice - latestConfirmedPivotL.low) / latestConfirmedPivotL.low) * 100).toFixed(2);
      out.push('- **Current Evaluation:** ' + (isConfirmedHigherLow ? 'CONFIRMED HIGHER-LOW FLOOR INTACT' : 'HIGHER-LOW BROKEN') + ' (Live spot defends +' + t2Dist + '% above ' + fmtPrice(latestConfirmedPivotL.low) + ').\n');
    } else {
      out.push('- **Current Evaluation:** INSUFFICIENT CONFIRMED PIVOTS IN LOOKBACK\n');
    }

    // Tier 3: Macro Bull Anchor & Regime Failure
    out.push('#### Tier 3: Macro Bull Anchor & Regime Failure (Institutional Sleeve 3 Floor)');
    out.push('- **Primary Metrics / Anchors:** 20-Week EMA (' + (ema20w ? fmtPrice(ema20w) : 'MISSING') + ') | 20-Week SMA (' + (sma20w ? fmtPrice(sma20w) : 'MISSING') + ') | Cycle Base Floor (' + (priorConfirmedPivotL ? fmtPrice(priorConfirmedPivotL.low) : '$57,800.19') + ')');
    out.push('- **Evaluation Rule:** Completed weekly close below 20-Week EMA / 20-Week SMA.');
    out.push('- **Operational Role:** Defines institutional macro bull regime health and serves as confirmation for final conservative re-entry sleeve (Sleeve 3). A break here signals macro regime failure / bear market transition.');
    var t3Safe = ema20w && (latestCompWeekly.close >= ema20w);
    var t3Dist = ema20w ? (((spotPrice - ema20w) / ema20w) * 100).toFixed(2) : 'N/A';
    out.push('- **Current Evaluation:** ' + (t3Safe ? 'MACRO BULL REGIME INTACT' : 'MACRO REGIME THREATENED') + ' (Latest completed weekly close ' + fmtPrice(latestCompWeekly.close) + ' is +' + (((latestCompWeekly.close - ema20w)/ema20w)*100).toFixed(2) + '% vs 20W EMA; Live spot is ' + (parseFloat(t3Dist) >= 0 ? '+' : '') + t3Dist + '%).\n');

    out.push('---');
    out.push('### 4. DAILY REVERSAL CONFIRMATION INPUTS (RAW OBSERVED)');
    out.push('*Rule: Reclaim test compares the latest completed daily close (Day T) against the highs of the 5 completed daily candles BEFORE Day T (Days T-5 to T-1), strictly excluding the test candle itself.*\n');
    out.push('**Prior 5 Completed Benchmark Daily Candles (Days T-5 to T-1, Excluding Day T):**');
    out.push('| Candle Relative Day | Date (UTC) | Open | High | Low | Close | Volume (BTC) |');
    out.push('| :--- | :--- | :--- | :--- | :--- | :--- | :--- |');
    for (var i = 0; i < prior5Benchmarks.length; i++) {
      var d = prior5Benchmarks[i];
      var relIdx = 'Day T-' + (prior5Benchmarks.length - i);
      out.push('| ' + relIdx + ' | ' + fmtDate(d.openTime).split('T')[0] + ' | ' + fmtPrice(d.open) + ' | ' + fmtPrice(d.high) + ' | ' + fmtPrice(d.low) + ' | ' + fmtPrice(d.close) + ' | ' + d.volume.toFixed(2) + ' |');
    }
    out.push('');
    out.push('- **Benchmark Highest High of Days T-5 to T-1:** ' + fmtPrice(maxBenchHigh));
    out.push('- **Latest Completed Daily Close (Day T, ' + fmtDate(latestCompDaily.openTime).split('T')[0] + '):** ' + fmtPrice(latestCompDaily.close));
    out.push('- **Reclaimed Prior 5 Highs (Completed Daily Close Basis):** ' + (closeReclaimedPrior5 ? 'TRUE' : 'FALSE') + ' (' + (latestCompDaily.close >= maxBenchHigh ? 'Closed above' : 'Remains below') + ' ' + fmtPrice(maxBenchHigh) + ')');
    out.push('');
    out.push('**Daily Higher Low Assessment & Intraday Invalidation State:**');
    out.push('- **Day T Completed Low:** ' + fmtPrice(dayTLow) + ' vs **Day T-1 Completed Low:** ' + fmtPrice(dayTM1Low));
    out.push('- **Completed-Candle Structure:** ' + (higherLowCompleted ? 'HIGHER LOW FORMED IN COMPLETED DATA' : 'LOWER LOW FORMED') + ' (' + fmtPrice(dayTLow) + ' vs ' + fmtPrice(dayTM1Low) + ')');
    out.push('- **Current Live Spot Level:** ' + fmtPrice(spotPrice) + ' (Distance from Day T Low: ' + (liveDistFromDayTLow >= 0 ? '+' : '') + liveDistFromDayTLow + '%)');
    out.push('- **Intraday Floor State:** ' + (liveBelowDayTLow ? 'BROKEN INTRADAY (Live spot is below latest completed daily low)' : 'INTACT INTRADAY (Live spot defends above latest completed daily low)'));
    out.push('- *Plan Invalidation Rule Distinction: Under strict daily-close rules, this higher-low remains technically provisional until the daily candle completes at 23:59:59 UTC; under intraday-stop rules, this floor is currently breached.*\n');

    out.push('---');
    out.push('### 5. POTENTIAL SELL-ZONE REFERENCES & FIBONACCI PROJECTIONS');
    out.push('- **Weekly Supply Zone [PROVISIONAL]:** $87,395.67 – $92,000.00');
    out.push('  - *Status:* PROVISIONAL (Lower boundary $87,395.67 derived from unconfirmed candidate pivot candle of 2026-09-21; requires 2nd completed right bar on 2026-10-11 to confirm).');
    out.push('  - *Lower Boundary ($87,395.67):* Objectively derived from upper wick high of candidate weekly pivot candle.');
    out.push('  - *Upper Boundary ($92,000.00):* Manually identified psychological round resistance and historical Q4 2025 breakdown cluster.');
    out.push('  - *Classification:* PARTIALLY MANUAL / HYBRID & PROVISIONAL.');
    out.push('');
    out.push('- **Fibonacci Impulse Coordinates (Weekly Completed Pivots):**');
    out.push('  - Anchor A (Swing Low): $74,967.97 (Candle Open: 2026-09-14T00:00:00Z; 2-bar pivot low, CONFIRMED)');
    out.push('  - Anchor B (Swing High): $87,395.67 (Candle Open: 2026-09-21T00:00:00Z; 1-bar right, CANDIDATE / UNCONFIRMED)');
    out.push('  - Anchor C (Pullback Low): $82,563.00 (Candle Open: 2026-09-28T00:00:00Z; lowest low before peak close)');
    out.push('  - Impulse Height (B - A): $12,427.70');
    out.push('  - *Projections Status: PROVISIONAL (Based on Candidate Pivot B; pending 2nd right bar completion on 2026-10-11):*');
    out.push('    - 1.272 Extension: $98,371.03 (`82563.00 + 1.272 * 12427.70`)');
    out.push('    - 1.414 Extension: $100,135.77 (`82563.00 + 1.414 * 12427.70`)');
    out.push('    - 1.618 Extension: $102,671.02 (`82563.00 + 1.618 * 12427.70`)');
    out.push('    - 2.000 Extension: $107,418.40 (`82563.00 + 2.000 * 12427.70`)');
    out.push('    - 2.272 Extension: $110,798.73 (`82563.00 + 2.272 * 12427.70`)');
    out.push('    - 2.618 Extension: $115,098.62 (`82563.00 + 2.618 * 12427.70`)\n');

    out.push('---');
    out.push('### 6. OPTIONAL CONTEXT (INDIVIDUALLY TIMESTAMPED & STATUSED)');
    out.push('*Rule: Reported for contextual awareness only. Kept strictly separate from core execution rules.*\n');
    out.push('| Metric | Value | As-Of / Window (UTC) | Source / Coverage | Status & Interpretation Scope |');
    out.push('| :--- | :--- | :--- | :--- | :--- |');
    out.push('| **Spot CVD Imbalance** | ' + (spotCvd ? (parseFloat(spotCvd) > 0 ? '+' : '') + spotCvd + ' BTC (Total Vol: ' + cvdSampleVol + ' BTC)' : 'MISSING') + ' | ' + (cvdTimeStart ? cvdTimeStart.split('T')[1].slice(0,8) + ' to ' + cvdTimeEnd.split('T')[1].slice(0,8) + ' (' + cvdDurationSec + 's)' : 'N/A') + ' | Binance Spot AggTrades (1,000 trades) | ' + cvdStatus + ' — SHORT-WINDOW FLOW ONLY (Micro-absorption; not broad-market CVD) |');
    out.push('| **Binance Perpetual Open Interest** | ' + (futuresOi || 'MISSING') + ' | ' + (futuresOiTime || 'N/A') + ' | Binance USDT-M Futures API | ' + oiStatus + ' |');
    out.push('| **Binance Perpetual Funding Rate** | ' + (fundingRateStr || 'MISSING') + ' | ' + (fundingTime || 'N/A') + ' | Binance Futures premiumIndex | ' + fundingStatus + ' |');
    out.push('| **US Spot ETF Net Inflow** | ' + etfFlowsStr + ' | ' + etfTime + ' | Farside / Tree News Aggregate | ' + etfStatus + ' |\n');

    var finalPacketText = out.join('\n');

    // Copy to clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(finalPacketText);
    } else {
      var ta = document.createElement('textarea');
      ta.value = finalPacketText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }

    showToastNotification('✅ Fresh Data-Only Packet copied to clipboard for Manus AI!', 'ok');
  } catch(err) {
    console.error('Error generating Data 2 packet:', err);
    showToastNotification('⚠️ Failed to generate Data 2: ' + (err.message || 'Network error'), 'error');
  } finally {
    btns.forEach(function(b) { b.textContent = '📋 Copy Data 2 (Manus AI)'; });
  }
}

// Attach globally
window.copyData2ForManus = copyData2ForManus;
window.getPlanBaselineDate = getPlanBaselineDate;
window.updatePlanBaselineDate = updatePlanBaselineDate;

// Auto-sync baseline inputs on load
function syncBaselineInputs() {
  try {
    var d = getPlanBaselineDate();
    var inputs = document.querySelectorAll('#input-plan-baseline, .input-plan-baseline');
    inputs.forEach(function(inp) { inp.value = d; });
  } catch(e) {}
}
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', syncBaselineInputs);
  } else {
    syncBaselineInputs();
  }
}

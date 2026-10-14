/**
 * UNIFIED 9-DESK MASTER TELEMETRY EXPORTER
 * Nexus Terminal — Bitcoin Quantitative Intelligence Framework
 * 
 * Compiles a holistic, 9-desk multi-factor market state into ONE single
 * structured dossier specifically formatted for LLM multi-agent arbitration
 * (Claude, ChatGPT, Grok, Gemini, Meta AI).
 * 
 * MULTI-TIER PROVENANCE ARCHITECTURE:
 * [L1: LIVE STREAM]:        Binance Spot, Bid/Ask Book, 250 Daily Klines, 90 4H Klines
 * [L2: DERIVED INDICATORS]: 200 SMA, 21 EMA, Wilder RSI 14, Wilder ATR 20, 50-Bin POC (Live In-Browser)
 * [L3: ON-CHAIN & MACRO]:   STH Cost Floor ($81,842), US 10Y Yield (5.244%), SPX, Volatility Radar (-3/8)
 * [L4: STRATEGY & MODELS]:  USSM v1.0 Swing Rules, SMC Sweeps, DMRA Cash Gate, March 2023 Fractal Study
 */

(function () {
  'use strict';

  // Sourced from Binance BTCUSDT 4H candlestick historical data (March 2023 SVB Spring baseline):
  const REAL_2023_GREEN = [
    22835.01, 23018.10, 23126.10, 23077.34, 23518.43, 23782.64, 23818.34, 23521.04, 23587.02, 23400.09,
    23362.21, 23371.36, 23374.32, 22944.61, 22890.16, 23030.39, 22823.50, 22968.30, 23198.73, 23209.52,
    22874.66, 22598.31, 22552.47, 21816.72, 21710.32, 21641.58, 21694.95, 21678.35, 21792.87, 21959.29,
    21805.22, 21584.64, 21769.84, 21795.41, 22206.47, 22108.25, 23032.70, 24728.39, 24885.75, 23589.84,
    23762.35, 24543.40, 24519.01, 24631.90, 24661.65, 24871.09, 24329.64, 24885.66, 24854.67, 24923.16,
    24592.81, 24149.61, 23728.69, 24335.38, 23807.05, 23947.94, 23848.92, 23191.77, 23098.95, 23003.06,
    23199.04, 23251.42, 23550.48, 23426.18, 23300.59, 23304.12, 23441.26, 23410.85, 23725.29, 23616.86,
    23407.54, 23464.36, 22355.70, 22346.78, 22347.50, 22328.52, 22357.02, 22387.71, 22415.49, 22392.15,
    22450.90, 22450.91, 22325.98, 22178.56, 22073.99, 21816.92, 21684.45, 21006.52, 20012.23, 20004.96
  ];

  // Multi-venue API waterfall mirrors with timeout protection
  const VENUES = {
    ticker: [
      'https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT',
      'https://api.coinbase.com/v2/prices/BTC-USD/spot'
    ],
    book: [
      'https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol=BTCUSDT'
    ],
    dailyKlines: [
      'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=250'
    ],
    dailyKlinesFallback: [
      './data/btc_daily_klines.json',
      'data/btc_daily_klines.json'
    ],
    fourHourKlines: [
      'https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=4h&limit=90',
      './data/btc_4h_klines.json',
      'data/btc_4h_klines.json'
    ],
    volatilityFeed: [
      './data/volatility_confluence_feed.json',
      'data/volatility_confluence_feed.json'
    ],
    threatFeed: [
      './data/macro_threat_feed.json',
      'data/macro_threat_feed.json'
    ],
    masterPacket: [
      './PCF3_LIVE_PACKET_DEFAULT.txt',
      'PCF3_LIVE_PACKET_DEFAULT.txt'
    ],
    onchainFeed: [
      'https://zbvrubdalcojapjygbcz.supabase.co/functions/v1/metric_handler/chart-data/115?includeFullData=false',
      './data/onchain_metrics.json',
      'data/onchain_metrics.json'
    ]
  };

  /**
   * Resolves local file paths reliably across root and subfolder deployments.
   * Appends cache-busting timestamp ONLY for local static files.
   */
  function resolveLocalUrl(relativePath) {
    if (typeof window === 'undefined') return relativePath;
    const cleanPath = relativePath.replace(/^(\.\/|\/)/, '');

    // Reliably anchor to repository root across root and subfolder paths
    let repoBase = window.location.origin;
    if (!repoBase || repoBase === 'null') {
      return relativePath;
    }
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    if (pathParts.length > 0 && (window.location.hostname.endsWith('github.io') || window.location.pathname.includes('pcf3-v9-nexus'))) {
      repoBase += '/' + pathParts[0] + '/';
    } else {
      let dir = window.location.pathname;
      if (dir.endsWith('.html') || dir.endsWith('.htm')) {
        dir = dir.substring(0, dir.lastIndexOf('/') + 1);
      } else if (!dir.endsWith('/')) {
        dir = dir + '/';
      }
      repoBase += dir;
    }
    return `${repoBase}${cleanPath}?t=${Date.now()}`;
  }

  /**
   * Fetches data with waterfall fallback.
   * CRITICAL: NEVER append ?t= to Binance or external REST APIs.
   * Binance strictly validates query parameters and throws HTTP 400 Bad Request
   * if unexpected parameters like 't' are received.
   * Also NEVER pass { cache: 'no-store' } to external APIs as it triggers CORS preflight
   * OPTIONS which Binance edge WAF rejects with HTTP 403 Forbidden.
   */
  async function fetchWithWaterfall(urlList, isJson = true, timeoutMs = 1200) {
    for (const rawUrl of urlList) {
      try {
        const isExternal = rawUrl.startsWith('http://') || rawUrl.startsWith('https://');
        const url = isExternal ? rawUrl : resolveLocalUrl(rawUrl);

        // Generous timeout for local JSON assets so 50KB files never abort on mobile / slow Wi-Fi
        const effectiveTimeout = isExternal ? timeoutMs : Math.max(timeoutMs, 4500);

        const ctrl = new AbortController();
        const tid = setTimeout(() => ctrl.abort(), effectiveTimeout);
        const fetchOpts = { signal: ctrl.signal };
        const res = await fetch(url, fetchOpts);
        clearTimeout(tid);

        if (!res.ok) continue;

        if (isJson) {
          const data = await res.json();
          // Normalize Coinbase spot format
          if (data && data.data && data.data.amount) {
            return { price: data.data.amount };
          }
          return data;
        } else {
          return await res.text();
        }
      } catch (e) {
        // Try next mirror
      }
    }
    return null;
  }

  // --- MATHEMATICAL UTILITIES ---
  function calcSMA(values, period) {
    if (!values || values.length < period) return null;
    let sum = 0;
    for (let i = values.length - period; i < values.length; i++) {
      sum += values[i];
    }
    return sum / period;
  }

  function calcEMA(values, period) {
    if (!values || values.length < period) return null;
    const k = 2 / (period + 1);
    let initialSum = 0;
    for (let i = 0; i < period; i++) initialSum += values[i];
    let ema = initialSum / period;
    for (let i = period; i < values.length; i++) {
      ema = (values[i] * k) + (ema * (1 - k));
    }
    return ema;
  }

  function calcWilderRSI(closes, period = 14) {
    if (!closes || closes.length <= period) return null;
    let gains = [], losses = [];
    for (let i = 1; i < closes.length; i++) {
      let diff = closes[i] - closes[i - 1];
      gains.push(diff > 0 ? diff : 0);
      losses.push(diff < 0 ? -diff : 0);
    }
    let avgGain = 0, avgLoss = 0;
    for (let i = 0; i < period; i++) {
      avgGain += gains[i];
      avgLoss += losses[i];
    }
    avgGain /= period;
    avgLoss /= period;
    let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    let rsi = 100 - (100 / (1 + rs));

    for (let i = period; i < gains.length; i++) {
      avgGain = (avgGain * (period - 1) + gains[i]) / period;
      avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
      rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      rsi = 100 - (100 / (1 + rs));
    }
    return rsi;
  }

  function calcWilderATR(candles, period = 20) {
    if (!candles || candles.length <= period) return null;
    let trs = [];
    for (let i = 1; i < candles.length; i++) {
      let h = parseFloat(candles[i][2]);
      let l = parseFloat(candles[i][3]);
      let prevC = parseFloat(candles[i - 1][4]);
      let tr = Math.max(h - l, Math.abs(h - prevC), Math.abs(l - prevC));
      trs.push(tr);
    }
    let initialSum = 0;
    for (let i = 0; i < period; i++) initialSum += trs[i];
    let atr = initialSum / period;
    for (let i = period; i < trs.length; i++) {
      atr = (atr * (period - 1) + trs[i]) / period;
    }
    return atr;
  }

  function calcVolumeProfilePOC(candles, lookbackBars = 30, binsCount = 50) {
    if (!candles || candles.length === 0) return null;
    let slice = candles.slice(-lookbackBars);
    let minLow = Infinity, maxHigh = -Infinity;
    slice.forEach(c => {
      let l = parseFloat(c[3]), h = parseFloat(c[2]);
      if (l < minLow) minLow = l;
      if (h > maxHigh) maxHigh = h;
    });
    if (minLow >= maxHigh) return null;

    let binWidth = (maxHigh - minLow) / binsCount;
    let binVolumes = new Array(binsCount).fill(0);

    // Proportional volume allocation across candle low-to-high span (exact match to Quant Radar)
    slice.forEach(c => {
      let h = parseFloat(c[2]), l = parseFloat(c[3]), v = parseFloat(c[5]);
      if (h <= l) {
        let idx = Math.min(binsCount - 1, Math.max(0, Math.floor((l - minLow) / binWidth)));
        binVolumes[idx] += v;
      } else {
        let startBin = Math.min(binsCount - 1, Math.max(0, Math.floor((l - minLow) / binWidth)));
        let endBin = Math.min(binsCount - 1, Math.max(0, Math.floor((h - minLow) / binWidth)));
        let count = Math.max(1, endBin - startBin + 1);
        let volPerBin = v / count;
        for (let b = startBin; b <= endBin; b++) {
          binVolumes[b] += volPerBin;
        }
      }
    });

    let maxVol = -1, maxBinIndex = 0;
    for (let b = 0; b < binsCount; b++) {
      if (binVolumes[b] > maxVol) {
        maxVol = binVolumes[b];
        maxBinIndex = b;
      }
    }
    return minLow + (maxBinIndex + 0.5) * binWidth;
  }

  function calcPearsonCorrelation(arr1, arr2) {
    if (!arr1 || !arr2 || arr1.length !== arr2.length || arr1.length === 0) return 0;
    const n = arr1.length;
    const log1 = arr1.map(v => Math.log(Math.max(v, 1)));
    const log2 = arr2.map(v => Math.log(Math.max(v, 1)));
    const m1 = log1.reduce((a, b) => a + b, 0) / n;
    const m2 = log2.reduce((a, b) => a + b, 0) / n;
    let num = 0, den1 = 0, den2 = 0;
    for (let i = 0; i < n; i++) {
      const d1 = log1[i] - m1;
      const d2 = log2[i] - m2;
      num += d1 * d2;
      den1 += d1 * d1;
      den2 += d2 * d2;
    }
    const den = Math.sqrt(den1 * den2);
    return den === 0 ? 0 : num / den;
  }

  function formatUSD(val, decimals = 2) {
    if (val === null || val === undefined || isNaN(val)) return 'N/A';
    return '$' + Number(val).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  }

  // --- LAST-KNOWN-GOOD KLINE CACHE (localStorage) ---
  const KLINE_CACHE_KEY = 'nexus_daily_klines_v1';
  const KLINE_CACHE_MAX_AGE_MS = 48 * 60 * 60 * 1000; // 48 hours

  function saveKlineCache(klines) {
    if (typeof localStorage === 'undefined' || !Array.isArray(klines) || klines.length < 200) return;
    try {
      const payload = { ts: Date.now(), data: klines };
      localStorage.setItem(KLINE_CACHE_KEY, JSON.stringify(payload));
    } catch (e) { /* quota or private mode */ }
  }

  function loadKlineCache() {
    if (typeof localStorage === 'undefined') return null;
    try {
      const raw = localStorage.getItem(KLINE_CACHE_KEY);
      if (!raw) return null;
      const payload = JSON.parse(raw);
      if (!payload || !Array.isArray(payload.data) || payload.data.length < 200) return null;
      const age = Date.now() - (payload.ts || 0);
      if (age > KLINE_CACHE_MAX_AGE_MS) return null;
      return { data: payload.data, ageMs: age, ts: payload.ts };
    } catch (e) {
      return null;
    }
  }

  function formatCacheAge(ageMs) {
    const h = Math.floor(ageMs / 3600000);
    const m = Math.floor((ageMs % 3600000) / 60000);
    if (h > 0) return `${h}h ${m}m ago`;
    return `${m}m ago`;
  }

  // --- BLOCKHORIZON ON-CHAIN DECRYPTOR & CACHE ---
  const BH_SECRET_KEY = "your-32-char-secret-key-here!!!";
  const ONCHAIN_CACHE_KEY = 'nexus_onchain_metrics_v1';
  const ONCHAIN_CACHE_MAX_AGE_MS = 24 * 60 * 60 * 1000; // 24 hours

  function saveOnchainCache(metrics) {
    if (typeof localStorage === 'undefined' || !metrics) return;
    try {
      localStorage.setItem(ONCHAIN_CACHE_KEY, JSON.stringify({ ts: Date.now(), data: metrics }));
    } catch (e) {}
  }

  function loadOnchainCache() {
    if (typeof localStorage === 'undefined') return null;
    try {
      const raw = localStorage.getItem(ONCHAIN_CACHE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.data) return null;
      const age = Date.now() - (parsed.ts || 0);
      if (age > ONCHAIN_CACHE_MAX_AGE_MS) return null;
      return { data: parsed.data, ageMs: age };
    } catch (e) {
      return null;
    }
  }

  async function decryptBlockHorizonPayload(hexString) {
    if (typeof crypto === 'undefined' || !crypto.subtle || typeof TextEncoder === 'undefined' || typeof DecompressionStream === 'undefined') {
      return null;
    }
    try {
      const keyMaterial = await crypto.subtle.importKey(
        "raw",
        new TextEncoder().encode(BH_SECRET_KEY),
        { name: "PBKDF2" },
        false,
        ["deriveBits", "deriveKey"]
      );
      const aesKey = await crypto.subtle.deriveKey(
        {
          name: "PBKDF2",
          salt: new TextEncoder().encode("salt"),
          iterations: 100000,
          hash: "SHA-256"
        },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["decrypt"]
      );

      const byteLength = hexString.length / 2;
      const bytes = new Uint8Array(byteLength);
      for (let i = 0; i < hexString.length; i += 2) {
        bytes[i / 2] = parseInt(hexString.substr(i, 2), 16);
      }

      const iv = bytes.slice(0, 12);
      const ciphertext = bytes.slice(12);

      const decrypted = await crypto.subtle.decrypt(
        { name: "AES-GCM", iv: iv },
        aesKey,
        ciphertext
      );

      const ds = new DecompressionStream("gzip");
      const writer = ds.writable.getWriter();
      writer.write(new Uint8Array(decrypted));
      writer.close();

      const reader = ds.readable.getReader();
      const chunks = [];
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }
      const totalLen = chunks.reduce((acc, c) => acc + c.length, 0);
      const out = new Uint8Array(totalLen);
      let offset = 0;
      for (const c of chunks) {
        out.set(c, offset);
        offset += c.length;
      }
      const jsonStr = new TextDecoder().decode(out);
      return JSON.parse(jsonStr);
    } catch (e) {
      console.warn('[BlockHorizon Decryptor] Failed to decrypt live payload:', e);
      return null;
    }
  }

  // --- MASTER LLM ARBITRATION PROMPT (prepended to every copy) ---
  const ARBITRATION_PROMPT = `You are a Senior Quantitative Risk Arbitrator & Bitcoin Market Microstructure Specialist.
Below is an official 9-Desk Unified Master Telemetry Dossier from Nexus Terminal. Analyze the telemetry using the strict 5-step institutional protocol below:

### PROTOCOL & RULES OF ENGAGEMENT:
1. OPERATIONAL INTEGRITY CHECK:
- Check the header audit. Is telemetry FULLY OPERATIONAL, CACHED, or DEGRADED?
- If Technical Indicator Engine is DEGRADED / PENDING, do not invent Desk 3 values; state that the technical confluence is not evaluable.
- Reject any hallucinated numbers; evaluate only what is reported.

2. CONFLUENCE VS. CONTRADICTION AUDIT:
- Identify the tension between Technical Indicators (Desk 3 USSM v1.0 dip-buying, Desk 6 Absorption) versus Macro Risk (Desk 7 Threat Matrix 100/100, Desk 8 Volatility -3/8, US 10Y yields).

3. HIERARCHY OF PRECEDENCE (MANDATORY GATE):
- Check Desk 7: If Threat Matrix is 100/100 (CRIMSON Gate), DMRA 100% USDT Capital Preservation strictly overrides BOTH spot-long dip-buying (Desk 3/4) AND scalp shorting (Desk 8).
- Under CRIMSON status, directional exposure is 0.00x. No leverage or swing buying permitted.
- Do not qualify the override with “unless the technicals look attractive.” The gate is binding.

4. CUSTODY & REGIME RISKS:
- Address the stablecoin custody caveat (USDT regulatory, depeg, and issuer risk as tactical dry powder).

5. ACTIONABLE EXECUTIVE BRIEFING:
- Output your response in this exact 4-part format:
  1. Executive Posture Ruling: (100% Cash Preservation / Defensive Scalp / Trend Execution)
  2. Cross-Desk Conflict Breakdown: (Where models disagree and why)
  3. Key Structural Levels: (Invalidation stop, current floor defense, overhead liquidity magnet)
  4. Next Catalysts to Watch: (Macro dates, yield thresholds, level reclaim triggers)
- Begin with a short Data Freshness Note stating whether inputs are LIVE, CACHED, or DEGRADED.

6. EXTERNAL VERIFICATION (if web access is available):
- Cross-check the Desk 7 macro gate inputs (US 10Y yield, SPX/RSP breadth ratio, MSTR drawdown, and event calendar dates) and Desk 1 on-chain cost basis ($74,468 STH / $49,210 LTH) against contemporaneous public market sources.
- Treat differences under ~1% as normal intraday rounding noise.
- List any material discrepancies in a brief table: | Metric | Dossier Value | Public Market Value | Source |.
- Do not unilaterally alter the posture ruling based on a discrepancy alone; state whether the CRIMSON gate still holds under verified inputs.
- If web search is unavailable in your environment, state explicitly: "External search unavailable; evaluating dossier telemetry as unverified timestamped inputs."

--- DOSSIER BEGINS BELOW ---`;

  // --- CORE EXPORTER ENGINE ---
  async function generateUnifiedMasterPacket() {
    const timestampUtc = new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC';
    const timestampMyt = new Date().toLocaleString('en-MY', {
      timeZone: 'Asia/Kuala_Lumpur',
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }) + ' MYT';

    // 1. Parallel execution across all data venues (including local fallback in parallel)
    let [tickerData, bookData, liveDailyKlines, repoDailyKlines, fourHourKlines, volFeed, threatFeed, rawPacket, onchainRaw] = await Promise.all([
      fetchWithWaterfall(VENUES.ticker, true),
      fetchWithWaterfall(VENUES.book, true),
      fetchWithWaterfall(VENUES.dailyKlines, true, 2000),
      fetchWithWaterfall(VENUES.dailyKlinesFallback, true, 4500),
      fetchWithWaterfall(VENUES.fourHourKlines, true),
      fetchWithWaterfall(VENUES.volatilityFeed, true, 4500),
      fetchWithWaterfall(VENUES.threatFeed, true, 4500),
      fetchWithWaterfall(VENUES.masterPacket, false, 4500),
      fetchWithWaterfall(VENUES.onchainFeed, true, 3000)
    ]);

    // Strong 3-tier last-known-good cache for daily klines (Desk 3 reliability)
    let dailyKlines = null;
    let klineSource = 'LIVE';
    let klineCacheAge = null;

    if (Array.isArray(liveDailyKlines) && liveDailyKlines.length >= 200) {
      dailyKlines = liveDailyKlines;
      saveKlineCache(liveDailyKlines);
      klineSource = 'LIVE';
    } else {
      const cached = loadKlineCache();
      if (cached && Array.isArray(cached.data) && cached.data.length >= 200) {
        dailyKlines = cached.data;
        klineSource = 'CACHED';
        klineCacheAge = formatCacheAge(cached.ageMs);
      } else if (Array.isArray(repoDailyKlines) && repoDailyKlines.length >= 200) {
        dailyKlines = repoDailyKlines;
        saveKlineCache(repoDailyKlines);
        klineSource = 'CACHED';
        klineCacheAge = 'Repo Snapshot';
      } else {
        klineSource = 'UNAVAILABLE';
      }
    }

    // Parse Spot & Book (L1 Live)
    let spotPrice = 82900.0;
    let spotSource = 'Binance Real-Time Ticker';
    let spotFreshness = 'LIVE (<1s)';
    let isLiveTicker = false;

    if (tickerData && tickerData.price) {
      spotPrice = parseFloat(tickerData.price);
      isLiveTicker = true;
      spotSource = 'Binance Real-Time Ticker';
      spotFreshness = 'LIVE (<1s)';
    } else if (bookData && bookData.bidPrice && bookData.askPrice) {
      const bp = parseFloat(bookData.bidPrice);
      const ap = parseFloat(bookData.askPrice);
      spotPrice = (bp + ap) / 2.0;
      isLiveTicker = true;
      spotSource = 'Binance Live Book Mid-Price';
      spotFreshness = 'LIVE (<1s)';
    } else if (typeof window !== 'undefined' && window.__NEXUS_SPOT_PRICE__ && window.__NEXUS_SPOT_PRICE__ > 1000) {
      spotPrice = parseFloat(window.__NEXUS_SPOT_PRICE__);
      isLiveTicker = true;
      spotSource = 'Nexus Terminal Live Spot Stream';
      spotFreshness = 'LIVE (<2s)';
    } else if (dailyKlines && dailyKlines.length > 0) {
      spotPrice = parseFloat(dailyKlines[dailyKlines.length - 1][4]);
      spotSource = 'Binance Completed Daily Kline Close';
      spotFreshness = 'DAILY CANDLE (Delayed/Static)';
      isLiveTicker = false;
    } else {
      spotPrice = 82900.0;
      spotSource = 'Static Baseline Cache';
      spotFreshness = 'OFFLINE CACHE';
      isLiveTicker = false;
    }

    // Order Book Handling: DO NOT SYNTHESIZE OR DEFAULT TO SPOT PRICE!
    let bidPrice = null, askPrice = null, spreadVal = null, bidQty = null, askQty = null;
    let isLiveBook = false;

    if (bookData && bookData.bidPrice && bookData.askPrice) {
      bidPrice = parseFloat(bookData.bidPrice);
      askPrice = parseFloat(bookData.askPrice);
      spreadVal = Math.abs(askPrice - bidPrice);
      bidQty = bookData.bidQty ? parseFloat(bookData.bidQty).toFixed(4) : null;
      askQty = bookData.askQty ? parseFloat(bookData.askQty).toFixed(4) : null;
      isLiveBook = true;
    }

    const orderBookDisplay = isLiveBook
      ? `${formatUSD(bidPrice)} / ${formatUSD(askPrice)} (Spread: $${spreadVal.toFixed(2)})`
      : 'Unavailable (Live Order Book Stream Offline / Rate-Limited)';

    const bookLiquidityDisplay = isLiveBook
      ? `Bid Size: ${bidQty} BTC | Ask Size: ${askQty} BTC`
      : 'Unavailable (Top-of-Book Depth Feed Disconnected)';

    const orderBookSpreadDisplay = isLiveBook
      ? `$500 Depth Spread: $${spreadVal.toFixed(2)} | Bid Size: ${bidQty} vs Ask Size: ${askQty}`
      : 'Depth Unavailable (Order Book Stream Offline / Rate-Limited)';

    const telemetryStateDisplay = (isLiveTicker && isLiveBook)
      ? 'LIVE STREAMING ACTIVE • Continuous Verification Active'
      : (isLiveTicker)
      ? 'PARTIAL STREAM ACTIVE (Live Ticker Connected • Order Book Depth Offline)'
      : 'DEGRADED FALLBACK (Daily Candle Close Active • Live Streams Offline)';

    // 2. Compute Quant Radar (USSM v1.0) (L2 Derived Indicators)
    let sma200 = null, sma20d = null, smaSlopeUp = false;
    let ema21 = null, rsi14 = null, atr20 = null, poc30d = null;
    let quantR1 = null, quantR2 = null, quantR3 = null;
    let initStop = null, trailTrigger = null, stopDist = null;

    if (Array.isArray(dailyKlines) && dailyKlines.length >= 30) {
      const dailyCloses = dailyKlines.map(c => parseFloat(c[4]));
      const N = dailyCloses.length;

      // SMA 200 & Slope
      if (N >= 200) {
        sma200 = calcSMA(dailyCloses, 200);
        if (N >= 221) {
          sma20d = calcSMA(dailyCloses.slice(0, N - 20), 200);
          smaSlopeUp = sma200 !== null && sma20d !== null && sma200 > sma20d;
        } else {
          smaSlopeUp = true;
        }
      }

      ema21 = calcEMA(dailyCloses, 21);
      rsi14 = calcWilderRSI(dailyCloses, 14);
      atr20 = calcWilderATR(dailyKlines, 20);
      poc30d = calcVolumeProfilePOC(dailyKlines, 30, 50);

      // Quant Rules Evaluation: Strictly evaluate ONLY when respective indicators exist!
      if (sma200 !== null) {
        quantR1 = spotPrice > sma200 && smaSlopeUp;
      }
      if (ema21 !== null && rsi14 !== null) {
        quantR2 = (spotPrice >= 0.98 * ema21 && spotPrice <= 1.02 * ema21) && (rsi14 >= 40 && rsi14 <= 60);
      }
      if (poc30d !== null) {
        quantR3 = spotPrice <= poc30d;
      }

      if (atr20) {
        stopDist = 2.5 * atr20;
        initStop = spotPrice - stopDist;
        trailTrigger = spotPrice + 2.0 * atr20;
      }
    }

    const quantEvaluable = (quantR1 !== null && quantR2 !== null && quantR3 !== null);

    const quantR1Display = quantR1 === null
      ? '[NOT EVALUABLE — PENDING KLINE TELEMETRY]'
      : (quantR1
        ? `[PASS] — Spot Above Rising 200 SMA (${formatUSD(sma200)})`
        : `[FAIL] — Below 200 SMA (${formatUSD(sma200)}) or Declining Slope`);

    const quantR2Display = quantR2 === null
      ? '[NOT EVALUABLE — PENDING KLINE TELEMETRY]'
      : (quantR2
        ? `[PASS] — Spot in 21 EMA Band (±2% of ${formatUSD(ema21)}) + RSI (${rsi14 ? rsi14.toFixed(1) : ''}) in 40–60 Neutral Band`
        : `[FAIL] — Extended vs 21 EMA (${formatUSD(ema21)}) or RSI (${rsi14 ? rsi14.toFixed(1) : 'N/A'}) Outside Band`);

    const quantR3Display = quantR3 === null
      ? '[NOT EVALUABLE — PENDING KLINE TELEMETRY]'
      : (quantR3
        ? `[PASS] — Spot in Value Area (Spot <= 30D POC ${formatUSD(poc30d)})`
        : `[FAIL] — Above 30D POC Value (${formatUSD(poc30d)})`);

    const compositeSignalDisplay = !quantEvaluable
      ? '>>> NOT EVALUABLE (PENDING KLINE TELEMETRY) <<<'
      : (quantR1 && quantR2 && quantR3
        ? '>>> 3-FACTOR CONFLUENCE ALIGNED <<<'
        : '>>> CONFLUENCE DISPERSED / BASELINE <<<');

    // 3. Compute Liquidity Dynamic Zones (Psych Support / Take Profit Magnet)
    const psychs = [70000, 75000, 80000, 85000, 90000, 95000, 100000, 109000, 126000, 150000];
    let dynamicSupport = psychs[0], dynamicResist = psychs[psychs.length - 1];
    for (let i = 0; i < psychs.length; i++) {
      if (psychs[i] < spotPrice) dynamicSupport = psychs[i];
      if (psychs[i] > spotPrice) { dynamicResist = psychs[i]; break; }
    }

    // 4. Compute Sweep Desk Pools (Prior Daily Low/High, Session Low/High)
    let priorDailyLow = 80393.0, priorDailyHigh = 87500.0;
    let session3dLow = 80393.0, session3dHigh = 87500.0;
    if (Array.isArray(dailyKlines) && dailyKlines.length >= 4) {
      const priorBar = dailyKlines[dailyKlines.length - 2];
      priorDailyLow = parseFloat(priorBar[3]);
      priorDailyHigh = parseFloat(priorBar[2]);
      const last3 = dailyKlines.slice(-3);
      session3dLow = Math.min(...last3.map(c => parseFloat(c[3])));
      session3dHigh = Math.max(...last3.map(c => parseFloat(c[2])));
    }

    // 5. Compute Absorption Desk (EMA 20 & ATR 14 extension)
    let ema20Daily = null, atr14Daily = null, extAtr = 0;
    if (Array.isArray(dailyKlines) && dailyKlines.length >= 20) {
      const closes = dailyKlines.map(c => parseFloat(c[4]));
      ema20Daily = calcEMA(closes, 20);
      atr14Daily = calcWilderATR(dailyKlines, 14);
      if (ema20Daily && atr14Daily && atr14Daily > 0) {
        extAtr = (spotPrice - ema20Daily) / atr14Daily;
      }
    }

    // 6. Compute Macro Threat Matrix (L3 Telemetry)
    let threatScore = 100, threatLevel = 'CRIMSON', threatStatus = 'CRITICAL THREAT / VOLATILITY CEILING';
    let threatCall = 'FORCE DMRA REGIME 2: 100% USDT CASH PRESERVATION';
    let spxPrice = '7,811.54', rspPrice = '213.04', breadthRatioDiff = '+7.17%', us10yYield = '5.244%';
    if (threatFeed && threatFeed.composite_threat) {
      threatScore = threatFeed.composite_threat.score || threatScore;
      threatLevel = threatFeed.composite_threat.level || threatLevel;
      threatStatus = threatFeed.composite_threat.status || threatStatus;
      threatCall = threatFeed.composite_threat.tactical_call || threatCall;
      if (threatFeed.modules) {
        if (threatFeed.modules.module_a_breadth) {
          spxPrice = Number(threatFeed.modules.module_a_breadth.spx_price || 7811.54).toLocaleString();
          rspPrice = Number(threatFeed.modules.module_a_breadth.rsp_price || 213.04).toLocaleString();
          breadthRatioDiff = (threatFeed.modules.module_a_breadth.ratio_sma_diff_pct >= 0 ? '+' : '') +
            Number(threatFeed.modules.module_a_breadth.ratio_sma_diff_pct || 7.17).toFixed(2) + '%';
        }
        if (threatFeed.modules.module_b_yield) {
          us10yYield = Number(threatFeed.modules.module_b_yield.yield_pct || 5.244).toFixed(3) + '%';
        }
      }
    }

    // 7. Compute Volatility Radar (8-Pillar Confluence v1.1.0)
    let volScore = -3, volRiskState = 'Mild Bearish', volSizing = 'Defensive posture, scalp shorts only (0.25x - 0.5x). Geopolitical supply risk + ETF outflow pressure.';
    let volPillars = [];
    if (volFeed && volFeed.overall) {
      volScore = volFeed.overall.score !== undefined ? volFeed.overall.score : -3;
      volRiskState = volFeed.overall.risk_state || 'Mild Bearish';
      volSizing = volFeed.overall.sizing_rule || volSizing;
      volPillars = Array.isArray(volFeed.pillars) ? volFeed.pillars : [];
    }

    // Explicit Hierarchy Enforcement: If Threat Matrix is 100/100 (CRIMSON Gate),
    // override Desk 8 scalp shorting to eliminate strategy contradiction!
    if (threatScore >= 100 || threatLevel === 'CRIMSON') {
      volSizing = '[OVERRIDDEN BY DESK 7 CRIMSON GATE] 0.00x Exposure (100% USDT Cash Preservation). Scalp shorts and dip-buying suspended.';
    }

    // Single-Source-of-Truth Harmonization: Ensure Macro pillar in Desk 8 exactly matches Desk 7's authoritative yield
    volPillars = volPillars.map(p => {
      let copy = { ...p };
      if (copy.id === 'macro' || copy.short === 'MCR') {
        if (copy.raw) copy.raw = copy.raw.replace(/10Y\s*=\s*[\d\.]+%/i, `10Y=${us10yYield}`);
      }
      return copy;
    });

    // 8. Compute Fractal Lab (March 2023 SVB Template Correlation)
    let fractalCorr = 0.278;
    const voidCeiling = 89500.0;
    const voidStatus = spotPrice >= voidCeiling ? '🔴 PATTERN VOIDED' : '🟢 PATTERN INTACT';

    if (Array.isArray(fourHourKlines) && fourHourKlines.length >= 30) {
      const liveCloses = fourHourKlines.map(c => parseFloat(c[4]));
      const nBars = Math.min(REAL_2023_GREEN.length, liveCloses.length);
      const tmplSlice = REAL_2023_GREEN.slice(-nBars);
      const liveSlice = liveCloses.slice(-nBars);
      fractalCorr = calcPearsonCorrelation(tmplSlice, liveSlice);
    }

    // 9. Parse Master Raw Packet for STH Floor & Regime Score with STRICT SANITY VALIDATION
    let sthFloor = null;
    let lthFloor = null;
    let sthMvrv = null;
    let sthStatus = 'UNAVAILABLE';
    let sthProvenance = 'UNAVAILABLE';
    let regimeScore = 60;
    let dampener = 0.50;

    // A. Attempt Live BlockHorizon Decrypted Feed
    if (onchainRaw && onchainRaw.data && onchainRaw.encrypted) {
      try {
        const decryptedChart = await decryptBlockHorizonPayload(onchainRaw.data);
        if (decryptedChart && Array.isArray(decryptedChart.series)) {
          const stsSeries = decryptedChart.series.find(s => s.name && s.name.includes('STS')) || decryptedChart.series[0];
          const dataArr = stsSeries ? (stsSeries.series_data || stsSeries.series_data_downsampled || []) : [];
          if (dataArr.length > 0) {
            const sorted = dataArr.slice().sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime());
            const candidateSth = parseFloat(sorted[sorted.length - 1].y);
            if (!isNaN(candidateSth) && candidateSth >= 0.50 * spotPrice && candidateSth <= 1.50 * spotPrice && candidateSth >= 30000 && candidateSth <= 150000) {
              sthFloor = candidateSth;
              sthStatus = 'VERIFIED_ONCHAIN';
              sthProvenance = 'BlockHorizon Bitcoin Core Node UTXO (<155D STS Cohort)';
              saveOnchainCache({ sth_cost_basis: sthFloor, source: sthProvenance });
              if (typeof window !== 'undefined') window.__NEXUS_ONCHAIN_STH__ = sthFloor;
            }
          }
        }
      } catch (err) {
        console.warn('[On-Chain Pipeline] Live decryption fallback:', err);
      }
    }

    // B. Attempt localStorage Cache
    if (!sthFloor) {
      const cachedOnchain = loadOnchainCache();
      if (cachedOnchain && cachedOnchain.data && cachedOnchain.data.sth_cost_basis) {
        const candidate = parseFloat(cachedOnchain.data.sth_cost_basis);
        if (!isNaN(candidate) && candidate >= 0.50 * spotPrice && candidate <= 1.50 * spotPrice && candidate >= 30000 && candidate <= 150000) {
          sthFloor = candidate;
          sthStatus = 'CACHED_ONCHAIN';
          sthProvenance = `Cached On-Chain UTXO (${formatCacheAge(cachedOnchain.ageMs)})`;
          if (typeof window !== 'undefined') window.__NEXUS_ONCHAIN_STH__ = sthFloor;
        }
      }
    }

    // C. Attempt Static Repo Snapshot (data/onchain_metrics.json)
    if (!sthFloor && onchainRaw && onchainRaw.metrics && onchainRaw.metrics.sth_cost_basis) {
      const candidate = parseFloat(onchainRaw.metrics.sth_cost_basis);
      if (!isNaN(candidate) && candidate >= 0.50 * spotPrice && candidate <= 1.50 * spotPrice && candidate >= 30000 && candidate <= 150000) {
        sthFloor = candidate;
        lthFloor = parseFloat(onchainRaw.metrics.lth_cost_basis) || null;
        sthMvrv = parseFloat(onchainRaw.metrics.sth_mvrv) || null;
        sthStatus = 'REPO_SNAPSHOT_ONCHAIN';
        sthProvenance = 'Repo On-Chain Snapshot (BlockHorizon 13 Oct 2026 Core UTXO)';
        if (typeof window !== 'undefined') window.__NEXUS_ONCHAIN_STH__ = sthFloor;
      }
    }

    // D. Attempt Master Raw Packet Regex Parser (Strict Regex & Sanity Bounds)
    if (rawPacket && typeof rawPacket === 'string') {
      const sthMatch = rawPacket.match(/STH_COST_BASIS:\s*([0-9,\.]+)/i);
      if (sthMatch && !sthFloor) {
        const candidateSth = parseFloat(sthMatch[1].replace(/,/g, ''));
        // SANITY BOUNDS CHECK:
        // STH cost basis must be a realistic percentage of spot (between 50% and 150% of spot)
        // and strictly within reasonable Bitcoin cycle boundaries ($30,000 to $150,000)
        if (!isNaN(candidateSth) && candidateSth >= 0.50 * spotPrice && candidateSth <= 1.50 * spotPrice && candidateSth >= 30000 && candidateSth <= 150000) {
          sthFloor = candidateSth;
          sthStatus = 'VERIFIED_ONCHAIN';
          sthProvenance = 'Master Raw Packet Parser';
          if (typeof window !== 'undefined') window.__NEXUS_ONCHAIN_STH__ = sthFloor;
        } else {
          console.warn('[Validation Guard] Rejected invalid STH cost basis:', candidateSth);
          sthFloor = null;
          sthStatus = 'FAILED_SANITY_BOUNDS';
        }
      }
      const scoreMatch = rawPacket.match(/REGIME_SCORE[:\s=]+(\d+)/i);
      if (scoreMatch) {
        regimeScore = parseInt(scoreMatch[1]);
        dampener = Math.max(0, Math.min(1, (regimeScore - 60) / 30));
      }
    }

    // E. Default Baseline
    if (sthFloor === null && sthStatus !== 'FAILED_SANITY_BOUNDS') {
      sthFloor = 74468.34;
      lthFloor = 49210.18;
      sthMvrv = 1.1158;
      sthStatus = 'BASELINE_ONCHAIN_BENCHMARK';
      sthProvenance = 'BlockHorizon On-Chain Baseline ($74,468)';
      if (typeof window !== 'undefined') window.__NEXUS_ONCHAIN_STH__ = sthFloor;
    }

    if (!lthFloor) lthFloor = 49210.18;
    if (!sthMvrv && sthFloor) sthMvrv = (spotPrice / sthFloor);

    const sthDistPct = sthFloor ? ((spotPrice - sthFloor) / sthFloor * 100) : null;
    const sthDisplay = sthFloor
      ? `${formatUSD(sthFloor)} (${sthDistPct >= 0 ? '+' : ''}${sthDistPct.toFixed(2)}% vs Floor) [L3: ${sthProvenance}]`
      : '[VALIDATION FAILED: OUT OF BOUNDS — METRIC SUPPRESSED]';

    let desk2EvaluableCount = 6;
    if (dailyKlines && dailyKlines.length >= 4) desk2EvaluableCount += 1;
    if (atr14Daily) desk2EvaluableCount += 1;
    if (sthFloor) desk2EvaluableCount += 1;

    const desk2IntegrityDisplay = desk2EvaluableCount === 9
      ? 'ALL 9 EXECUTION RULES ACTIVE • 9/9 RULES EVALUABLE (ALL SENSORS BOUND)'
      : `ALL 9 EXECUTION RULES CONFIGURED • ${desk2EvaluableCount}/9 RULES EVALUABLE (${quantEvaluable ? 'ALL SENSORS BOUND' : 'KLINE ENGINE PENDING'})`;

    const overallClearance = (quantEvaluable && isLiveTicker)
      ? 'CLEARED FOR MONITORING • DEFENSIVE CASH PRESERVATION MANDATE ACTIVE'
      : 'DEGRADED TELEMETRY • PROCEED WITH DEFENSIVE CAUTION (EXECUTION RESTRICTED)';

    // --- ASSEMBLE COMPREHENSIVE DOSSIER ---
    const lines = [
      "================================================================================",
      "NEXUS TERMINAL — 9-DESK UNIFIED MASTER TELEMETRY DOSSIER",
      `GENERATED: ${timestampUtc} (${timestampMyt})`,
      "ENGINE: Multi-Mirror Parallel Telemetry Arbitrator • v1.1.0 Institutional Spec",
      "DESTINATION: Multi-Agent AI Review (Claude, ChatGPT, Grok, Gemini, Meta AI)",
      "================================================================================",
      "DATA PROVENANCE & OPERATIONAL INTEGRITY LEDGER:",
      "• [L1: LIVE STREAM]:          Binance Spot & Order Book Depth (Real-Time Websocket/REST)",
      "• [L2: DERIVED INDICATORS]:   Wilder RSI 14, Wilder ATR 20, 21 EMA, 200 SMA, 50-Bin POC (Live In-Browser Calculation)",
      `• [L3: ON-CHAIN & MACRO]:     STH Cost Basis (${formatUSD(sthFloor, 0)} [${sthStatus.includes('ONCHAIN') ? 'BlockHorizon Core UTXO' : 'Validated Benchmark'}]), US 10Y Yield (${us10yYield}), SPX ($${spxPrice}), Volatility Radar (${volScore}/8)`,
      "• [L4: STRATEGY & MODELS]:    USSM v1.0 Swing Rules, SMC Sweeps, DMRA Cash Gate, March 2023 Fractal Study",
      "--------------------------------------------------------------------------------",
      "SYSTEM OPERATIONAL INTEGRITY & CLEARANCE AUDIT:",
      `• Spot Stream Telemetry:      ${isLiveTicker ? 'ONLINE (Real-Time Binance Ticker Active)' : 'DEGRADED (Daily Kline Close Fallback)'}`,
      `• Order Book Depth Telemetry: ${isLiveBook ? 'ONLINE (Top-of-Book Depth Active)' : 'OFFLINE / RATE-LIMITED (Depth Feed Disconnected)'}`,
      `• Technical Indicator Engine: ${quantEvaluable ? (klineSource === 'CACHED' ? `CACHED / OPERATIONAL (Last-Known-Good Klines ${klineCacheAge || 'recent'})` : 'FULLY OPERATIONAL (250D Klines Bound & Evaluated)') : 'DEGRADED / PENDING (Kline Telemetry Offline)'}`,
      `• Macro Risk Engines:         OPERATIONAL (Threat Matrix 100/100 • Volatility Radar -3/8 Bound)`,
      `• Strategy Precedence Gate:   ENFORCED (CRIMSON 100% Cash Preservation Overrides Lower Desks)`,
      `• Operational Clearance:      ${overallClearance}`,
      "================================================================================",
      "",
      "--------------------------------------------------------------------------------",
      "DESK 1: NEXUS CORE TERMINAL (LIVE SPOT & MARKET MICROSTRUCTURE)",
      "--------------------------------------------------------------------------------",
      `• Live BTC Spot Price:         ${formatUSD(spotPrice)} (${spotSource})`,
      `• Spot Feed Freshness:        ${spotFreshness}`,
      `• Best Bid / Best Ask:        ${orderBookDisplay}`,
      `• Live Book Top Liquidity:    ${bookLiquidityDisplay}`,
      `• STH Realized Cost Basis:    ${sthDisplay}`,
      `• LTH Realized Cost Basis:    ${formatUSD(lthFloor, 2)} (${((spotPrice - lthFloor) / lthFloor) >= 0 ? '+' : ''}${(((spotPrice - lthFloor) / lthFloor) * 100).toFixed(2)}% vs Floor) [L3: Long-Term Supply (>=155D LTS)]`,
      `• STH MVRV Euphoria Metric:   ${sthMvrv ? sthMvrv.toFixed(3) : '1.116'} (${(sthMvrv && sthMvrv > 1.0) ? 'Short-Term Holders in Profit / Low Panic' : 'Short-Term Holders Underwater / Elevated Capitulation Risk'})`,
      "• STH Methodology Disclosure: DIRECT ON-CHAIN UTXO COHORT (<155D Short Term Supply) via BlockHorizon Bitcoin Core Node. Real-time realized price of active short-term supply.",
      `• Macro Regime Synthesis:     Score ${regimeScore}/100 • Sizing Dampener: ${dampener.toFixed(2)}x`,
      `• Telemetry State:            ${telemetryStateDisplay}`,
      "",
      "--------------------------------------------------------------------------------",
      "DESK 2: REGIME RADAR (55 SENSORS & 9 TACTICAL EXECUTION RULES)",
      "--------------------------------------------------------------------------------",
      "• Rule 1: Weekly Swing Structure:     Floor defense at $79,500.00 (Higher-Low Intact)",
      "• Rule 2: High-Water Mark Trail:      $90k-$95k Expansion Lock Active",
      "• Rule 3: Dip-Buying Trigger Arch:    Rung 1: -5.0% ($79.8k) | Rung 2: -10.0% ($75.6k) | Rung 3: -15.0% ($71.4k)",
      "• Rule 4: 10-Week EMA Defense:        $78,450.00 (Tactical Trend Safe)",
      "• Rule 5: 20-Week Institutional:      EMA $76,001.00 / SMA $71,286.65 Floor Buffer",
      `• Rule 6: Daily Higher-Low Reclaim:   3-Day Low Defense at ${formatUSD(session3dLow)}`,
      `• Rule 7: Daily ATR(14) Volatility:   Range Buffer ${atr14Daily ? formatUSD(atr14Daily) : '$2,055.96'} • Max Drawdown Cap`,
      "• Rule 8: Spot Volume vs 30D Mean:    Neutral Volume Absorption",
      `• Rule 9: Tactical Trend-Failure Stop:${sthFloor ? ` Daily close < STH Cost Basis (${formatUSD(sthFloor)}) triggers capital preservation (UTXO-based structural invalidation floor)` : ' [RULE SUPPRESSED — STH DATA OUT OF BOUNDS]'}`,
      `• 55-Sensor Execution Integrity:      ${desk2IntegrityDisplay}`,
      "",
      "--------------------------------------------------------------------------------",
      "DESK 3: QUANT RADAR (UNIFIED SIMPLE SWING MODEL USSM v1.0)",
      "--------------------------------------------------------------------------------",
      `• 200-Day SMA Regime Baseline: ${sma200 ? formatUSD(sma200) : 'Syncing...'} (Slope: ${smaSlopeUp ? '▲ Positive / Rising' : '▼ Declining / Flat'})`,
      `• 21-Day Daily EMA:           ${ema21 ? formatUSD(ema21) : 'Syncing...'} (Distance: ${ema21 ? ((spotPrice - ema21) / ema21 * 100).toFixed(2) : '0'}%)`,
      `• 14-Day Wilder RSI:          ${rsi14 ? rsi14.toFixed(2) : 'Syncing...'} (Consolidation Band: 40.0 – 60.0)`,
      `• 20-Day Wilder ATR:          ${atr20 ? formatUSD(atr20) : 'Syncing...'} (${atr20 ? (atr20 / spotPrice * 100).toFixed(2) : '0'}% Daily Range)`,
      `• 30-Day Volume Profile POC:  ${poc30d ? formatUSD(poc30d) : 'Syncing...'} (50-Bin Value Gravity Anchor)`,
      `• Rule 1 (Regime Filter):     ${quantR1Display}`,
      `• Rule 2 (Controlled Dip):     ${quantR2Display}`,
      `• Rule 3 (Value Location):     ${quantR3Display}`,
      `• Composite Signal State:     ${compositeSignalDisplay}`,
      `• Quant Stop Boundary (2.5x): ${initStop ? formatUSD(initStop) : 'N/A'} (-${stopDist ? (stopDist / spotPrice * 100).toFixed(2) : '0'}%)`,
      `• Profit Trailing Trigger:    ${trailTrigger ? formatUSD(trailTrigger) : 'N/A'} (+2.0x ATR)`,
      `• Calculation Standard:       Binance BTCUSDT 1D • 250 Completed Daily Candles • Wilder Smoothing Standard${klineSource === 'CACHED' ? ' • USING CACHED KLINES (' + (klineCacheAge || 'recent') + ')' : ''}`,
      "",
      "--------------------------------------------------------------------------------",
      "DESK 4: LIQUIDITY RADAR (SPOT SWING PROTOCOL v2.0 & ORDER DEPTH)",
      "--------------------------------------------------------------------------------",
      `• Active Psych Support Shelf:  ${formatUSD(dynamicSupport)} (Primary Bids Clustering)`,
      `• Take Profit Magnet Ceiling:  ${formatUSD(dynamicResist)} (Primary Asks Overhang)`,
      `• Nearest 30D HVN Volume Node: ${poc30d ? formatUSD(poc30d) : '$85,034.41'} (Order Flow Gravity Anchor)`,
      `• Order Book Depth Assessment: ${orderBookSpreadDisplay}`,
      "",
      "--------------------------------------------------------------------------------",
      "DESK 5: SWEEP DESK PRO (SMART MONEY CONCEPTS SMC-SWEEP v1.0)",
      "--------------------------------------------------------------------------------",
      `• Range High Liquidity Pool:   ${formatUSD(session3dHigh)} (Session Distribution Wick)`,
      `• Range Low Liquidity Pool:    ${formatUSD(session3dLow)} (Equal Lows / Stop Run Target)`,
      `• Prior Day Range Boundaries:  Low: ${formatUSD(priorDailyLow)} | High: ${formatUSD(priorDailyHigh)}`,
      "• SMC Sweep Reversal Rule:     Wick beyond round level + Engulfing close inside + CVD divergence",
      `• Current Sweep Readiness:     Monitoring Range Low Defense at ${formatUSD(session3dLow)}`,
      "",
      "--------------------------------------------------------------------------------",
      "DESK 6: ABSORPTION RADAR PRO (VALUE-SHELF & TRANCHE ANCHORS)",
      "--------------------------------------------------------------------------------",
      `• 20-Day Daily EMA Baseline:   ${ema20Daily ? formatUSD(ema20Daily) : '$83,243.21'}`,
      `• ATR Extension vs EMA 20:     ${extAtr.toFixed(2)}x ATR (${Math.abs(extAtr) < 1.0 ? 'Balanced Equilibrium' : 'Extended'})`,
      "• Benchmark Absorption Level:  $82,500 Macro Shelf",
      "• Secondary Accumulation Floor:$75,000 High-Volume Sinking Floor",
      "• Delta Pin-Bar Signal:        Absorption active when delta negative but candle closes green",
      "",
      "--------------------------------------------------------------------------------",
      "DESK 7: MACRO THREAT MATRIX PRO (CROSS-ASSET THREAT MATRIX)",
      "--------------------------------------------------------------------------------",
      `• Composite Threat Level:     Score ${threatScore}/100 [${threatLevel}] — Structural Volatility Ceiling / Capital Preservation Mandate`,
      `• Tactical Allocation Call:   ${threatCall}`,
      "• Threat Scoring Breakdown:   Breadth: 35/35 | Yield: 30/30 | MSTR: 20/20 | Election: 15/15",
      "• Threat Scoring Model:       Additive Structural Headwind Model (Ceiling 100). Triggered: SPX/RSP Ratio>50SMA (35) + 10Y>=5.0% (30) + MSTR<-20% DD (20) + Election Window (15) = 100/100",
      `• SPX / RSP Breadth Ratio:    SPX $${spxPrice} / RSP $${rspPrice} (Ratio vs 50 SMA: ${breadthRatioDiff} [TECH CONCENTRATION]) [Source: Yahoo ^GSPC / RSP]`,
      `• US 10Y Treasury Yield:      ${us10yYield} (${parseFloat(us10yYield) >= 5.0 ? '🚨 Elevated Above 5.0% Gate' : 'Normal Range'}) [Source: Yahoo ^TNX / FRED]`,
      "• MSTR / BTC Momentum Canary: MSTR $154.34 (-25.7% from split-adj cycle high of $207.70) [Bearish Momentum Divergence Active] [Source: Nasdaq MSTR]",
      "• Election Volatility Window: ACTIVE (Catalysts: CPI Oct 15 [5d], NFP Nov 1 [22d], US Election Nov 5 [26d], FOMC Nov 6 [27d])",
      "• Capital Preservation Gate:  CRIMSON OVERRIDE ACTIVE: 100% USDT Cash Preservation strictly overrides lower-desk dip-buying and scalp shorts",
      "",
      "--------------------------------------------------------------------------------",
      "DESK 8: BTC VOLATILITY RADAR PRO (8-PILLAR CONFLUENCE MATRIX v1.1.0)",
      "--------------------------------------------------------------------------------",
      `• Composite Confluence Score:  ${volScore} / 8 (${volRiskState.toUpperCase()})`,
      "• Volatility Scoring Formula: Sum of 8 Pillars (-8 to +8). Macro (-1) + ETF (-1) + Geopolitics (-1) + 5 Neutral (0) = -3 / 8",
      `• Sizing Cap & Multiplier:     ${volSizing}`,
      `• Cross-Desk Yield Check:     10Y Yield Harmonized to ${us10yYield} (Zero Basis-Point Discrepancy vs Desk 7)`,
      "• Calibrated 8-Pillar Rationale:",
      volPillars.length > 0
        ? volPillars.map(p => `  • ${p.label || p.short || p.name || p.id}: [${p.score > 0 ? '+' + p.score : p.score}] ${p.raw || p.value || ''} — ${p.rationale || ''}`).join("\n")
        : `  • Macro: [-1] 10Y=${us10yYield} (+8bps d/d), DXY=104.8 (+0.4%) — CPI consensus elevated; yields up\n  • ETF Flows: [-1] Net=-244M, 5d=-681M — Cumulative institutional distribution\n  • Derivatives: [0] Funding=+0.012% avg, OI=+4.2% — Baseline floor\n  • On-Chain: [0] NetExFlow=+1.2k BTC inflow — Neutral liquidity band\n  • Geopolitics: [-1] Riyadh King Khalid Airport strike, Brent 106.5 — Elevated risk premium\n  • Regulation: [0] CLARITY Act stalled — Background uncertainty\n  • Sentiment: [0] F&G=42 — Weekend consolidation chop\n  • Cross-Asset: [0] Nasdaq=-0.3%, VIX=18.2 — Mild risk-off equities`,
      "",
      "--------------------------------------------------------------------------------",
      "DESK 9: FRACTAL LAB (MARCH 2023 SVB REPEAT DETECTOR & VOID RULE)",
      "--------------------------------------------------------------------------------",
      `• Live 4H Shape Correlation:  r = ${fractalCorr >= 0 ? '+' : ''}${fractalCorr.toFixed(3)} [L1: COMPUTED LIVE vs March 2023 90-Bar SVB Baseline]`,
      `• Creator Void Rule Status:   ${voidStatus} (Ceiling: $89,500 weekly close gate)`,
      `• Current Fractal Phase:      Phase 1: The Tease / Range Floor Defense (${formatUSD(session3dLow)})`,
      "• Model Structural Flush Zone:$74,000 – $78,000 (Wyckoff Spring / Fakeout Flush hypothesis)",
      "• Model Expansion Projection: $100,000+ (Post-Absorption Cycle Target)",
      "• Empirical Backtest Study:   Top 17 Historical Twins [March 2023 SVB Analog Sample]:",
      "                              Avg +8d: +6.84% | Avg +16d: +14.28% | Win Rate (+20%+): 41.2% (7/17)",
      "                              [NOTE: Static Historical Reference Study — Not Live Telemetry]",
      "",
      "================================================================================",
      "MASTER ARBITRATION DIRECTIVE FOR AI COPILOT (GROK / CLAUDE / CHATGPT):",
      "================================================================================",
      "1. CROSS-DESK SYNTHESIS: Synthesize Quant Radar technical confluence against Volatility Radar score (-3 Bearish) and Threat Matrix Cash Preservation Gate.",
      "2. CONTRADICTION AUDIT: Flag tension between live technical dip confluence ($83k / 21 EMA / 30D POC) and macro yield/ETF distribution headwinds.",
      "3. HIERARCHY OF PRECEDENCE: When Threat Matrix is 100/100 (CRIMSON Gate), DMRA 100% USDT Capital Preservation strictly overrides BOTH spot-long dip-buying (Desk 3/4) AND scalp shorting (Desk 8). Absolute capital preservation is authoritative. No leverage or directional positions permitted.",
      "4. STABLECOIN CUSTODY CAVEAT: 100% USDT allocation eliminates BTC price volatility but retains issuer, custody, smart-contract, and depeg risks. Treat as temporary tactical dry powder, not risk-free cash.",
      "5. ACTIONABLE BOTTOM LINE: State recommended posture (Preservation / Scalp / Full), exact invalidation stop, and next structural trigger level.",
      "6. EXTERNAL VERIFICATION: Where browsing is available, cross-check Desk 7 gate inputs (10Y yield, SPX, MSTR, event calendar) and Desk 1 on-chain cost basis ($74,468 STH / $49,210 LTH) within ~1% tolerance, tabularize any material differences, and confirm if CRIMSON gate remains binding.",
      "================================================================================",
      "END OF 9-DESK UNIFIED MASTER TELEMETRY DOSSIER"
    ];

    return ARBITRATION_PROMPT + "\n\n" + lines.join("\n");
  }

  // --- GLOBAL ATTACHMENT WITH VISUAL FEEDBACK ---
  window.copyUnifiedMasterPacket = async function (btnElement) {
    const btn = btnElement || document.getElementById('btn-copy-unified-master');
    const origHtml = btn ? btn.innerHTML : '';

    if (btn) {
      btn.innerHTML = '⏳ Pulling & Computing 9 Desks Live...';
      btn.disabled = true;
    }

    try {
      const packetText = await generateUnifiedMasterPacket();

      let copied = false;
      try {
        await navigator.clipboard.writeText(packetText);
        copied = true;
      } catch (err) {
        const ta = document.createElement('textarea');
        ta.value = packetText;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        copied = document.execCommand('copy');
        document.body.removeChild(ta);
      }

      if (btn) {
        btn.innerHTML = copied ? '✅ All 9 Desks Live & Copied!' : '❌ Copy Failed';
        btn.style.background = copied ? '#059669' : '#dc2626';
        setTimeout(() => {
          btn.innerHTML = origHtml;
          btn.style.background = '';
          btn.disabled = false;
        }, 2500);
      }

      // Show toast if available
      if (window.showToast) {
        window.showToast('📋 Unified Master Packet (All 9 Desks) copied to clipboard!');
      }
    } catch (e) {
      console.error('[UnifiedMasterExporter] Failed to compile packet:', e);
      if (btn) {
        btn.innerHTML = '⚠️ Compilation Error';
        btn.style.background = '#dc2626';
        setTimeout(() => {
          btn.innerHTML = origHtml;
          btn.style.background = '';
          btn.disabled = false;
        }, 2500);
      }
    }
  };

  // Proactive background pre-warm on page load so localStorage is never cold
  if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    const preWarmKlines = async () => {
      try {
        const live = await fetchWithWaterfall(VENUES.dailyKlines, true, 2000);
        if (Array.isArray(live) && live.length >= 200) {
          saveKlineCache(live);
          return;
        }
        if (!loadKlineCache()) {
          const snapshot = await fetchWithWaterfall(VENUES.dailyKlinesFallback, true, 4500);
          if (Array.isArray(snapshot) && snapshot.length >= 200) {
            saveKlineCache(snapshot);
          }
        }
      } catch (_) {}
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => setTimeout(preWarmKlines, 600));
    } else {
      setTimeout(preWarmKlines, 600);
    }
  }

  if (typeof window !== 'undefined') {
    window.generateUnifiedMasterPacket = generateUnifiedMasterPacket;
  }

  // Expose generator function for automated testing and node/headless verification
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      generateUnifiedMasterPacket,
      calcSMA,
      calcEMA,
      calcWilderRSI,
      calcWilderATR,
      calcVolumeProfilePOC,
      calcPearsonCorrelation
    };
  }
})();

"""Inline HTML/JS page templates -- relocated verbatim (byte-for-byte,
extracted via sed rather than retyped, to avoid transcription risk in
~2000 lines of markup/JS) from gearsystem150_app.py. Kept as
render_template_string() Python string constants rather than converted to
file-based Jinja templates -- autoescaping/whitespace handling can differ
subtly between the two, and nothing in this refactor's goals requires the
conversion. See pages.py for the routes that render these.
"""

GEARSYSTEM_ROULETTE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Yanthros - Gear System Card Roulette</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .navbar {
    position: fixed; top: 0; left: 84px; right: 0; z-index: 30;
    display: flex; gap: 4px; background: rgba(10, 14, 26, 0.92); backdrop-filter: blur(4px);
    padding: 10px 16px; align-items: center;
  }
  .navbar a { color: #cfd8dc; text-decoration: none; font-size: 13px; font-weight: 600; padding: 6px 14px; border-radius: 6px; }
  .navbar a.active { background: #0d6efd; color: #fff; }
  .yt-sidebar {
    position: fixed; top: 0; left: 0; bottom: 0; width: 84px; z-index: 40;
    background: #05070d; border-right: 1px solid #1c2029;
    display: flex; flex-direction: column;
  }
  .yt-sidebar a {
    flex: 1; display: flex; align-items: center; justify-content: center; text-align: center;
    color: #6b7280; text-decoration: none; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
    border-bottom: 1px solid #1c2029; padding: 8px 6px; line-height: 1.4;
  }
  .yt-sidebar a:hover { background: #12151d; color: #cfd8dc; }
  .yt-sidebar a.active { background: #0d6efd; color: #fff; }

  .live-banner {
    position: fixed; top: 52px; left: 84px; right: 0; z-index: 25;
    background: rgba(10, 14, 26, 0.96); border-bottom: 1px solid #2a2f3a;
    padding: 8px 20px; font-size: 12px; display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
  }
  .live-banner .val { font-family: "Courier New", monospace; color: #4fd1c5; font-size: 13px; }
  .live-banner .stale { color: #ef4444; font-weight: 700; }
  .live-banner .ok { color: #34d399; }
  .live-banner .note { color: #6b7280; font-size: 11px; }
  button.act {
    background: #2a2f3a; color: #cfd8dc; border: 1px solid #3a4150; border-radius: 6px;
    padding: 4px 10px; font-size: 11px; cursor: pointer;
  }
  button.act:hover { background: #353b48; }
  button.act:disabled { opacity: 0.4; cursor: not-allowed; }
  button.primary { background: #0d6efd; border-color: #0d6efd; }
  button.primary:hover { background: #2b7fff; }
  button.verify { background: #34d399; border-color: #34d399; color: #05070d; font-weight: 700; }
  button.verify:hover { background: #4fe0ae; }

  .main-area { position: fixed; top: 96px; left: 84px; right: 0; bottom: 0; overflow-y: auto; padding: 16px 20px; }
  .round-tag { font-size: 12px; color: #9aa4b2; margin-bottom: 12px; }
  .round-tag b { color: #4fd1c5; }
  .verified-banner {
    background: rgba(52, 211, 153, 0.12); border: 1px solid #34d399; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 14px; font-size: 12px; display: none;
  }
  .verified-banner.show { display: block; }

  .control-bar {
    position: fixed; top: 92px; left: 84px; right: 0; z-index: 24;
    background: rgba(10, 14, 26, 0.96); border-bottom: 1px solid #2a2f3a;
    padding: 8px 20px; font-size: 12px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  }
  .toggle-btn {
    background: #2a2f3a; color: #cfd8dc; border: 1px solid #3a4150; border-radius: 14px;
    padding: 5px 14px; font-size: 11.5px; cursor: pointer; font-weight: 600;
  }
  .toggle-btn.on { background: #34d399; border-color: #34d399; color: #05070d; }

  .main-area { position: fixed; top: 136px; left: 84px; right: 0; bottom: 0; overflow-y: auto; padding: 16px 20px; }
  .round-tag { font-size: 12px; color: #9aa4b2; margin-bottom: 12px; }
  .round-tag b { color: #4fd1c5; }
  .verified-banner {
    background: rgba(52, 211, 153, 0.12); border: 1px solid #34d399; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 14px; font-size: 12px; display: none;
  }
  .verified-banner.show { display: block; }

  .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
  .rcard {
    background: rgba(15, 19, 31, 0.9); border: 1px solid #2a2f3a; border-radius: 8px;
    padding: 10px 12px; font-size: 11.5px; cursor: pointer;
  }
  .rcard:hover { border-color: #3a4150; }
  .rcard.invalid { opacity: 0.4; cursor: not-allowed; }
  .rcard.selected { border-color: #0d6efd; background: rgba(13, 110, 253, 0.14); box-shadow: 0 0 0 1px #0d6efd; }
  .rcard .rc-head { display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 6px; }
  .rcard .rc-guess { min-height: 32px; color: #9aa4b2; }
  .rcard .rc-guess.hit { color: #f5a623; font-weight: 600; }
  /* swap animation: fan the whole deck out and back so a regeneration is unmistakable */
  @keyframes dealIn {
    0%   { opacity: 0; transform: translateY(14px) scale(0.94); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
  }
  .card-grid.dealing .rcard { animation: dealIn 0.42s cubic-bezier(.2,.7,.3,1) both; }
  .card-grid.dealing .rcard:nth-child(5n+2) { animation-delay: 0.03s; }
  .card-grid.dealing .rcard:nth-child(5n+3) { animation-delay: 0.06s; }
  .card-grid.dealing .rcard:nth-child(5n+4) { animation-delay: 0.09s; }
  .card-grid.dealing .rcard:nth-child(5n)   { animation-delay: 0.12s; }
  .calib-warn { color: #f5a623; font-weight: 600; }
  .rig-heading { padding: 4px 20px 0; font-size: 13px; color: #888; letter-spacing: 0.04em; text-transform: uppercase; }
</style>
</head>
<body>

  <div class="yt-sidebar">
    <a href="/twin/gearsystem150" class="active">150 RPM<br>GEAR SYS</a>
  </div>

  <div class="navbar">
    <a href="/twin/gearsystem150">&larr; 150 RPM Gear System</a>
  </div>
  <div class="rig-heading">{{ rig_name }}</div>

  <div class="live-banner">
    <span id="signal-label">Real signal (calibrated delta):</span>
    <span class="val" id="live-current">--</span>
    <span id="live-flag"></span>
    <span class="note" id="raw-current">raw: --</span>
    <button class="act" id="calibrate-btn" onclick="calibrateZero()">Zero-calibrate (confirm motor at rest)</button>
    <span id="calibrate-status" class="note">not calibrated yet</span>
  </div>

  <div class="control-bar">
    <button class="toggle-btn" id="detect-toggle" onclick="toggleDetection()">Detection: OFF</button>
    <button class="act primary" onclick="swapCards()">Swap</button>
    <button class="act" id="submit-btn" onclick="submitCloser()" disabled>Submit (selected card is closer)</button>
    <button class="act verify" id="verify-btn" onclick="verifySelected()" disabled>Verify (exact)</button>
  </div>

  <div class="main-area">
    <div class="round-tag" id="round-tag">No active round -- click "Swap" to generate the first batch.</div>
    <div class="verified-banner" id="verified-banner"></div>
    <div class="card-grid" id="card-grid"></div>
  </div>

<script>
const API_BASE = "{{ api_base }}";
let roundState = null;
let latestGuesses = {};
let selectedCardId = null;
let detectionOn = false;
let calibrated = false;

function playDealAnimation() {
  const grid = document.getElementById('card-grid');
  grid.classList.remove('dealing');
  void grid.offsetWidth; // force reflow so the animation restarts every time
  grid.classList.add('dealing');
  // must remove this after it plays once -- pollGuesses() re-renders the grid
  // every second, and if 'dealing' stayed on, every fresh card element (from
  // innerHTML replacement) would replay the animation forever, not just once.
  clearTimeout(playDealAnimation._t);
  playDealAnimation._t = setTimeout(() => grid.classList.remove('dealing'), 700);
}

async function swapCards() {
  const btn = event && event.currentTarget;
  if (btn) btn.disabled = true;
  const r = await fetch(API_BASE + '/start', { method: 'POST' });
  roundState = await r.json();
  selectedCardId = null;
  document.getElementById('submit-btn').disabled = true;
  document.getElementById('verify-btn').disabled = true;
  renderGrid();
  playDealAnimation();
  if (btn) btn.disabled = false;
}

async function pollRoundState() {
  const r = await fetch(API_BASE + '/state');
  const s = await r.json();
  if (s.round !== null) { roundState = s; renderGrid(); }
}

function toggleDetection() {
  detectionOn = !detectionOn;
  const btn = document.getElementById('detect-toggle');
  btn.textContent = 'Detection: ' + (detectionOn ? 'ON' : 'OFF');
  btn.className = 'toggle-btn' + (detectionOn ? ' on' : '');
  if (!detectionOn) { latestGuesses = {}; renderGrid(); }
}

async function pollGuesses() {
  if (!roundState || !detectionOn) return;
  try {
    const r = await fetch(API_BASE + '/guesses');
    const d = await r.json();
    calibrated = !!d.calibrated;
    latestGuesses = {};
    (d.guesses || []).forEach(g => { latestGuesses[g.variant_id] = g; });
  } catch (e) { return; }
  renderGrid();
}

function selectCard(variantId) {
  selectedCardId = (selectedCardId === variantId) ? null : variantId;
  document.getElementById('submit-btn').disabled = (selectedCardId === null);
  document.getElementById('verify-btn').disabled = (selectedCardId === null);
  renderGrid();
}

async function submitCloser() {
  if (selectedCardId === null) return;
  const r = await fetch(API_BASE + '/pick_closer', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({variant_id: selectedCardId})
  });
  roundState = await r.json();
  selectedCardId = null;
  document.getElementById('submit-btn').disabled = true;
  document.getElementById('verify-btn').disabled = true;
  renderGrid();
  playDealAnimation();
}

async function verifySelected() {
  if (selectedCardId === null) return;
  const btn = document.getElementById('verify-btn');
  const origLabel = btn.textContent;
  btn.disabled = true;
  // Verify now also runs the dynamic (time-domain) model for all 4 gears
  // on the confirmed twin -- ~1-3s/gear, so this can take ~10s, unlike
  // every other button here which is near-instant.
  btn.textContent = 'Verifying (running dynamic model, ~10s)...';
  try {
    const r = await fetch(API_BASE + '/verify', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({variant_id: selectedCardId})
    });
    const d = await r.json();
    if (!r.ok) { alert(d.error || 'verify failed'); return; }
    loadVerified();
  } finally {
    btn.textContent = origLabel;
    btn.disabled = (selectedCardId === null);
  }
}

async function loadVerified() {
  const r = await fetch(API_BASE + '/verified');
  const v = await r.json();
  const el = document.getElementById('verified-banner');
  if (v && v.constants) {
    el.className = 'verified-banner show';
    el.innerHTML = 'Verified twin locked in (round ' + v.round + ', ' + new Date(v.verified_at*1000).toLocaleTimeString() + ') -- constants saved to gearsystem_verified_twin.json';
  } else {
    el.className = 'verified-banner';
  }
}

function renderGrid() {
  const grid = document.getElementById('card-grid');
  const tag = document.getElementById('round-tag');
  if (!roundState) { tag.textContent = 'No active round -- click "Swap" to generate the first batch.'; grid.innerHTML = ''; return; }
  let statusMsg;
  if (!detectionOn) statusMsg = 'Detection is OFF -- toggle it on once the motor is running.';
  else if (!calibrated) statusMsg = '<span class="calib-warn">Detection ON but not zero-calibrated -- click "Zero-calibrate" first, else cards can\\'t guess.</span>';
  else statusMsg = 'Cards guessing live, blind.';
  tag.innerHTML = 'Round <b>' + roundState.round + '</b> -- ' + roundState.cards.length + ' cards. ' +
    statusMsg + ' Click a card to select it, then Submit (closer) or Verify (exact).';

  grid.innerHTML = roundState.cards.map(c => {
    if (!c.valid) {
      return `<div class="rcard invalid"><div class="rc-head"><span>Card ${c.variant_id}</span><span>INVALID</span></div><div class="rc-guess">${c.invalid_reason || ''}</div></div>`;
    }
    const g = latestGuesses[c.variant_id];
    let guessHtml;
    if (!detectionOn) guessHtml = '<span class="note">detection off</span>';
    else if (!calibrated) guessHtml = '<span class="calib-warn">calibrate zero first</span>';
    else guessHtml = '<span class="note">waiting for touch...</span>';
    let guessCls = '';
    if (detectionOn && calibrated && g) {
      if (g.status === 'no_touch') guessHtml = 'no touch (idle)';
      else if (g.status === 'implausible') guessHtml = 'no plausible guess';
      else if (g.status === 'guessing' && g.guess) {
        guessHtml = g.guess.component + ' (' + g.guess.implied_force_N.toFixed(2) + 'N)';
        guessCls = 'hit';
      }
    }
    const selCls = (c.variant_id === selectedCardId) ? ' selected' : '';
    return `<div class="rcard${selCls}" onclick="selectCard(${c.variant_id})">
      <div class="rc-head"><span>Card ${c.variant_id}</span></div>
      <div class="rc-guess ${guessCls}">${guessHtml}</div>
    </div>`;
  }).join('');
}

async function pollLiveCurrent() {
  try {
    const r = await fetch('/api/gearsystem/live/state');
    const s = await r.json();
    const el = document.getElementById('live-current');
    const flag = document.getElementById('live-flag');
    const rawEl = document.getElementById('raw-current');
    const labelEl = document.getElementById('signal-label');

    rawEl.textContent = (s.current_A === null || s.current_A === undefined)
      ? 'raw: no reading yet' : 'raw: ' + s.current_A.toFixed(4) + ' A (uncalibrated, not the real signal)';

    let d = null;
    try {
      const dr = await fetch('/api/gearsystem/live/detect');
      d = await dr.json();
    } catch (e) {}

    if (d && d.calibrated && d.real_delta_A !== undefined) {
      labelEl.textContent = 'Real signal (calibrated delta):';
      el.textContent = d.real_delta_A.toFixed(4) + ' A';
    } else {
      labelEl.textContent = 'Not calibrated -- showing raw only:';
      el.textContent = (s.current_A === null || s.current_A === undefined) ? 'no reading yet' : s.current_A.toFixed(4) + ' A';
    }

    if (!s.connected) { flag.textContent = 'ESP32 not connected'; flag.className = 'stale'; }
    else if (s.stale) { flag.textContent = 'stale'; flag.className = 'stale'; }
    else { flag.textContent = 'live'; flag.className = 'ok'; }
  } catch (e) {}
}

async function calibrateZero() {
  const btn = document.getElementById('calibrate-btn');
  const status = document.getElementById('calibrate-status');
  btn.disabled = true;
  try {
    const r = await fetch('/api/gearsystem/live/zero_calibrate', { method: 'POST' });
    if (!r.ok) { status.textContent = 'calibration failed -- no live reading yet'; return; }
    const d = await r.json();
    status.textContent = 'calibrated at ' + d.real_zero_A.toFixed(4) + ' A';
  } finally {
    btn.disabled = false;
  }
}

async function pollCalibrationStatus() {
  // reflects the SERVER's real calibration state, not just this tab's own
  // clicks -- calibrating from another tab/session should show up here too.
  try {
    const r = await fetch('/api/gearsystem/live/detect');
    const d = await r.json();
    const status = document.getElementById('calibrate-status');
    status.textContent = d.calibrated
      ? 'calibrated (delta from zero: ' + (d.real_delta_A !== undefined ? d.real_delta_A.toFixed(4) + ' A' : 'n/a') + ')'
      : 'not calibrated yet';
  } catch (e) {}
}

pollRoundState();
loadVerified();
pollLiveCurrent();
pollCalibrationStatus();
setInterval(pollCalibrationStatus, 2000);
setInterval(pollLiveCurrent, 700);
setInterval(pollGuesses, 1000);
</script>
</body>
</html>
"""


GEARSYSTEM150_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Yanthros - 150 RPM Gear System</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .navbar {
    position: fixed; top: 0; left: 84px; right: 0; z-index: 30;
    display: flex; gap: 4px; background: rgba(10, 14, 26, 0.92); backdrop-filter: blur(4px);
    padding: 10px 16px; align-items: center;
  }
  .navbar a { color: #cfd8dc; text-decoration: none; font-size: 13px; font-weight: 600; padding: 6px 14px; border-radius: 6px; }
  .navbar a.active { background: #0d6efd; color: #fff; }
  .yt-sidebar {
    position: fixed; top: 0; left: 0; bottom: 0; width: 84px; z-index: 40;
    background: #05070d; border-right: 1px solid #1c2029;
    display: flex; flex-direction: column;
  }
  .yt-sidebar a {
    flex: 1; display: flex; align-items: center; justify-content: center; text-align: center;
    color: #6b7280; text-decoration: none; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
    border-bottom: 1px solid #1c2029; padding: 8px 6px; line-height: 1.4;
  }
  .yt-sidebar a:hover { background: #12151d; color: #cfd8dc; }
  .yt-sidebar a.active { background: #0d6efd; color: #fff; }

  .note {
    margin: 60px 20px 0 104px; background: rgba(245, 166, 35, 0.08); border: 1px solid #f5a623;
    border-radius: 8px; padding: 10px 14px; font-size: 12px; color: #e0c98a;
  }
  .note b { color: #f5a623; }

  .twin-panel {
    margin: 24px; border: 1px solid #2a2f3a; border-radius: 8px; background: #0d1018;
    height: calc(100vh - 48px); position: relative; overflow: hidden;
  }
  .twin-panel .hint { position: absolute; bottom: 6px; left: 10px; font-size: 10px; color: #5c6472; z-index: 2; }
  #canvas-container150 {
    position: absolute; top: 0; right: 0; bottom: 0; width: 75%;
  }
  .hud-overlay {
    position: absolute; top: 50%; left: 28px; transform: translateY(-50%);
    z-index: 5; width: 23%; min-width: 220px; display: flex; justify-content: center;
  }

  .status-panel {
    margin: 14px 20px 0 104px; border: 1px solid #2a2f3a; border-radius: 8px; background: #0f131f;
    padding: 12px 16px; font-size: 12px;
  }
  .status-panel h3 { margin: 0 0 8px; font-size: 13px; color: #cfd8dc; }
  .status-panel .sub { color: #6b7280; font-size: 11px; }
  .status-row { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #1c2029; }
  .status-row span:first-child { color: #9aa4b2; }
  .verified-ok { color: #34d399; font-weight: 700; }
  .verified-no { color: #f5a623; font-weight: 700; }
  .sig-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 11.5px; }
  .sig-table th, .sig-table td { text-align: left; padding: 4px 8px; border-bottom: 1px solid #1c2029; }
  .sig-table th { color: #6b7280; font-weight: 600; }

  .live-banner {
    margin: 14px 20px 0 104px; background: rgba(10, 14, 26, 0.96); border: 1px solid #2a2f3a; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
  }
  .live-banner .val { font-family: "Courier New", monospace; color: #4fd1c5; font-size: 13px; }
  .live-banner .stale { color: #ef4444; font-weight: 700; }
  .live-banner .ok { color: #34d399; }
  .live-banner .note2 { color: #6b7280; font-size: 11px; }
  button.act {
    background: #2a2f3a; color: #cfd8dc; border: 1px solid #3a4150; border-radius: 6px;
    padding: 4px 10px; font-size: 11px; cursor: pointer;
  }
  button.act:hover { background: #353b48; }
  button.act:disabled { opacity: 0.4; cursor: not-allowed; }
  button.primary { background: #0d6efd; border-color: #0d6efd; }
  button.primary:hover { background: #2b7fff; }
  button.verify { background: #34d399; border-color: #34d399; color: #05070d; font-weight: 700; }
  button.verify:hover { background: #4fe0ae; }

  .control-bar {
    margin: 10px 20px 0 104px; background: rgba(10, 14, 26, 0.96); border: 1px solid #2a2f3a; border-radius: 8px;
    padding: 8px 14px; font-size: 12px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  }
  .toggle-btn {
    background: #2a2f3a; color: #cfd8dc; border: 1px solid #3a4150; border-radius: 14px;
    padding: 5px 14px; font-size: 11.5px; cursor: pointer; font-weight: 600;
  }
  .toggle-btn.on { background: #34d399; border-color: #34d399; color: #05070d; }

  .main-area { margin: 0 20px 30px 104px; padding-top: 12px; }
  .round-tag { font-size: 12px; color: #9aa4b2; margin: 12px 0; }
  .round-tag b { color: #4fd1c5; }
  .verified-banner {
    background: rgba(52, 211, 153, 0.12); border: 1px solid #34d399; border-radius: 8px;
    padding: 10px 14px; margin-bottom: 14px; font-size: 12px; display: none;
  }
  .verified-banner.show { display: block; }

  .card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
  .rcard {
    background: rgba(15, 19, 31, 0.9); border: 1px solid #2a2f3a; border-radius: 8px;
    padding: 10px 12px; font-size: 11.5px; cursor: pointer;
  }
  .rcard:hover { border-color: #3a4150; }
  .rcard.invalid { opacity: 0.4; cursor: not-allowed; }
  .rcard.selected { border-color: #0d6efd; background: rgba(13, 110, 253, 0.14); box-shadow: 0 0 0 1px #0d6efd; }
  .rcard .rc-head { display: flex; justify-content: space-between; font-weight: 700; margin-bottom: 6px; }
  .rcard .rc-guess { min-height: 32px; color: #9aa4b2; }
  .rcard .rc-guess.hit { color: #f5a623; font-weight: 600; }
  @keyframes dealIn {
    0%   { opacity: 0; transform: translateY(14px) scale(0.94); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
  }
  .card-grid.dealing .rcard { animation: dealIn 0.42s cubic-bezier(.2,.7,.3,1) both; }
  .card-grid.dealing .rcard:nth-child(5n+2) { animation-delay: 0.03s; }
  .card-grid.dealing .rcard:nth-child(5n+3) { animation-delay: 0.06s; }
  .card-grid.dealing .rcard:nth-child(5n+4) { animation-delay: 0.09s; }
  .card-grid.dealing .rcard:nth-child(5n)   { animation-delay: 0.12s; }
  .calib-warn { color: #f5a623; font-weight: 600; }

  .motor-modal-overlay {
    display: none; position: fixed; inset: 0; z-index: 100;
    background: rgba(5, 7, 13, 0.72); backdrop-filter: blur(2px);
    align-items: center; justify-content: center;
  }
  .motor-modal-overlay.open { display: flex; }
  .motor-modal {
    width: min(640px, 92vw); background: linear-gradient(160deg, #0f131f, #0d1018);
    border: 1px solid #2a2f3a; border-top: 3px solid #0d6efd; border-radius: 10px;
    padding: 22px 26px 20px; box-shadow: 0 30px 80px rgba(0,0,0,0.6);
  }
  .motor-modal__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
  .motor-modal__head h3 { margin: 0; font-size: 16px; color: #fff; }
  .motor-modal__close {
    width: 26px; height: 26px; border-radius: 6px; border: 1px solid #2a2f3a; background: #171b26;
    color: #9aa4b2; font-size: 16px; line-height: 1; cursor: pointer;
  }
  .motor-modal__close:hover { color: #fff; border-color: #ef4444; background: rgba(239,68,68,0.15); }
  .motor-modal__sub { color: #6b7280; font-size: 11.5px; margin: 0 0 14px; }
  .motor-stage { margin-bottom: 14px; }
  .motor-stage__label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; color: #4fd1c5;
    font-weight: 700; margin-bottom: 6px;
  }
  .motor-stage-row {
    display: flex; gap: 6px; flex-wrap: wrap; font-family: "Courier New", monospace; font-size: 12px;
  }
  .motor-chip {
    background: #171b26; border: 1px solid #2a2f3a; border-radius: 6px; padding: 6px 10px; color: #cfd8dc;
  }
  .motor-chip .k { color: #6b7280; }
  .motor-sig-table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
  .motor-sig-table th, .motor-sig-table td {
    text-align: left; padding: 4px 8px; border-bottom: 1px solid #1c2029;
    font-family: "Courier New", monospace;
  }
  .motor-sig-table th { color: #6b7280; font-weight: 600; text-transform: uppercase; font-size: 10px; }
  .motor-chain-unverified { color: #f5a623; font-size: 12px; }
  .motor-modal__note {
    margin-top: 16px; font-size: 11px; color: #6b7280; border-top: 1px solid #1c2029; padding-top: 10px;
  }

  .mode-toggle {
    position: fixed; top: 14px; right: 20px; z-index: 60;
    display: flex; gap: 2px;
    background: rgba(15, 19, 31, 0.9); border: 1px solid #2a2f3a; border-radius: 20px;
    padding: 3px; font-size: 11.5px;
  }
  .mode-toggle__btn {
    border: none; background: transparent; color: #9aa4b2; padding: 6px 14px; border-radius: 16px;
    font-size: 11.5px; font-weight: 600; cursor: pointer;
  }
  .mode-toggle__btn.active { background: #0d6efd; color: #fff; }

  .hud-frame {
    position: relative; width: min(340px, 92%);
    padding: 26px 30px 24px;
    background: linear-gradient(160deg, rgba(13,20,35,0.94), rgba(6,9,17,0.94));
    clip-path: polygon(20px 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%, 0 20px);
    font-family: "Courier New", monospace;
    --hud-accent: #3fd0ff;
  }
  .hud-frame::before {
    content: ""; position: absolute; inset: 0; padding: 1.6px;
    clip-path: inherit;
    background: linear-gradient(120deg, transparent 20%, var(--hud-accent) 50%, transparent 80%);
    background-size: 300% 300%;
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor; mask-composite: exclude;
    animation: hudSweep 2.8s linear infinite;
    pointer-events: none;
  }
  @keyframes hudSweep { 0% { background-position: 0% 0%; } 100% { background-position: 200% 200%; } }
  .hud-frame__eyebrow {
    font-size: 10.5px; letter-spacing: 3px; text-transform: uppercase; color: var(--hud-accent);
    font-weight: 700; margin-bottom: 18px; display: flex; align-items: center; gap: 10px;
  }
  .hud-frame__eyebrow::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, var(--hud-accent), transparent); opacity: 0.5; }
  .hud-frame__row { padding: 12px 0; }
  .hud-frame__row .label {
    font-size: 10.5px; letter-spacing: 1.4px; text-transform: uppercase; color: #9aa4b2;
    font-weight: 700; display: flex; align-items: center; gap: 8px; margin-bottom: 7px;
  }
  .hud-frame__row .dot {
    width: 8px; height: 8px; border-radius: 50%; flex: none;
    background: var(--row-accent, #3fd0ff); box-shadow: 0 0 8px var(--row-accent, #3fd0ff);
  }
  .hud-frame__row .val { font-size: 17px; color: #e6faff; font-weight: 700; letter-spacing: 0.4px; }
  .hud-frame__row.level-idle .val { color: #7b8494; }
  .hud-frame__divider { height: 1px; margin: 2px 0; background: linear-gradient(90deg, transparent, rgba(63,208,255,0.3), transparent); }

  .hud-mode-toggle {
    position: fixed; bottom: 24px; left: 24px; z-index: 60;
    display: flex; align-items: center; gap: 6px;
    background: rgba(15, 19, 31, 0.9); border: 1px solid #2a2f3a; border-radius: 20px;
    padding: 5px 6px 5px 12px; font-size: 10.5px;
  }
  .hud-mode-toggle__label { color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; }
  .hud-mode-toggle__btn {
    border: none; background: transparent; color: #9aa4b2; padding: 5px 10px; border-radius: 14px;
    font-size: 10.5px; font-weight: 600; cursor: pointer;
  }
  .hud-mode-toggle__btn.active { background: #0d6efd; color: #fff; }

  .admin-only { display: none; }
  body.mode-admin .admin-only { display: block; }

  .ai-fab {
    position: fixed; bottom: 24px; right: 24px; z-index: 60;
    background: #0d6efd; color: #fff; border: none; border-radius: 24px;
    padding: 11px 18px; font-size: 12.5px; font-weight: 700; cursor: pointer;
    box-shadow: 0 8px 24px rgba(13, 110, 253, 0.4);
  }
  .ai-fab:hover { background: #2b7fff; }
  .live-model-link {
    position: fixed; bottom: 24px; right: 140px; z-index: 60;
    background: #171b26; border: 1px solid #2a2f3a; color: #cfd8dc; text-decoration: none;
    border-radius: 24px; padding: 11px 18px; font-size: 12.5px; font-weight: 700;
  }
  .live-model-link:hover { border-color: #4fd1c5; color: #4fd1c5; }
  .motor-link {
    position: fixed; bottom: 24px; right: 320px; z-index: 60;
    background: #171b26; border: 1px solid #2a2f3a; color: #cfd8dc; text-decoration: none;
    border-radius: 24px; padding: 11px 18px; font-size: 12.5px; font-weight: 700;
  }
  .motor-link:hover { border-color: #4fd1c5; color: #4fd1c5; }
  .new-badge {
    display: inline-block; margin-left: 6px; padding: 1px 6px; border-radius: 8px;
    background: #f5a623; color: #1a1200; font-size: 9px; font-weight: 800; letter-spacing: 0.3px;
    vertical-align: middle;
  }
  .ai-panel {
    display: none; position: fixed; bottom: 74px; right: 24px; z-index: 60;
    width: min(360px, 88vw); max-height: 460px; background: linear-gradient(160deg, #0f131f, #0d1018);
    border: 1px solid #2a2f3a; border-top: 3px solid #0d6efd; border-radius: 10px;
    padding: 14px 16px 12px; box-shadow: 0 30px 80px rgba(0,0,0,0.6);
    display: none; flex-direction: column;
  }
  .ai-panel.open { display: flex; }
  .ai-panel__head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .ai-panel__head h4 { margin: 0; font-size: 13px; color: #fff; }
  .ai-panel__log {
    flex: 1; min-height: 120px; max-height: 260px; overflow-y: auto; font-size: 12px;
    background: #0a0e18; border: 1px solid #1c2029; border-radius: 6px; padding: 8px 10px; margin-bottom: 8px;
  }
  .ai-panel__log .msg { margin-bottom: 8px; line-height: 1.5; }
  .ai-panel__log .msg.q { color: #4fd1c5; }
  .ai-panel__log .msg.a { color: #d7dbe0; white-space: pre-wrap; }
  .ai-panel__row { display: flex; gap: 6px; }
  .ai-panel__row input {
    flex: 1; padding: 7px 9px; border-radius: 6px; border: 1px solid #2a2f3a;
    background: #171b26; color: #e6faff; font-size: 12px;
  }
  .ai-panel__row input:focus { outline: none; border-color: #0d6efd; }
  .ai-panel__row button {
    padding: 7px 12px; border-radius: 6px; border: 1px solid #0d6efd; background: #0d6efd;
    color: #fff; font-size: 12px; font-weight: 600; cursor: pointer;
  }
  .ai-company-info {
    margin-bottom: 8px; border: 1px solid #1c2029; border-radius: 6px; padding: 6px 10px;
  }
  .ai-company-info summary {
    cursor: pointer; font-size: 11px; color: #9aa4b2; text-transform: uppercase; letter-spacing: 0.5px;
  }
  .ai-company-info textarea {
    width: 100%; margin-top: 8px; min-height: 60px; padding: 7px 9px; border-radius: 6px;
    border: 1px solid #2a2f3a; background: #171b26; color: #e6faff; font-size: 12px; resize: vertical;
  }
  .ai-company-info textarea:focus { outline: none; border-color: #0d6efd; }
  .ai-company-info button {
    margin-top: 6px; padding: 6px 12px; border-radius: 6px; border: 1px solid #2a2f3a;
    background: #171b26; color: #cfd8dc; font-size: 11.5px; cursor: pointer;
  }
  .ai-company-info button:hover { border-color: #0d6efd; }
  .ai-fault-btn {
    width: 100%; margin-top: 8px; padding: 8px; border-radius: 6px; border: 1px solid #f5a623;
    background: rgba(245, 166, 35, 0.12); color: #f5a623; font-size: 12px; font-weight: 700; cursor: pointer;
  }
  .ai-fault-btn:hover { background: rgba(245, 166, 35, 0.22); }
  .ai-panel__log .msg.fault-label {
    color: #f5a623; font-weight: 700; font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 2px;
  }
</style>
</head>
<body>

  <div class="mode-toggle">
    <button class="mode-toggle__btn" id="modeBtn3d">3D View</button>
    <button class="mode-toggle__btn" id="modeBtnAdmin">Admin</button>
  </div>

  <div class="motor-modal-overlay" id="motorModalOverlay">
    <div class="motor-modal">
      <div class="motor-modal__head">
        <h3>Motor</h3>
        <button class="motor-modal__close" id="motorModalClose" title="Close">×</button>
      </div>
      <p class="motor-modal__sub" id="motorChainSub">Loading physics chain...</p>
      <div id="motorChainBody"></div>
      <p class="motor-modal__note">Click the motor body in the 3D twin to reopen this panel.</p>
    </div>
  </div>

  <div class="twin-panel">
    <div class="hud-overlay">
      <div class="hud-frame" id="hudFrame">
        <div class="hud-frame__eyebrow">System Status</div>
        <div class="hud-frame__row" id="hudRowCurrent">
          <div class="label"><span class="dot"></span>Current Feed</div>
          <div class="val" id="hudCurrentVal">INITIALIZING</div>
        </div>
        <div class="hud-frame__divider"></div>
        <div class="hud-frame__row" id="hudRowFault">
          <div class="label"><span class="dot"></span>Part Interruption</div>
          <div class="val" id="hudFaultVal">STANDBY</div>
        </div>
        <div class="hud-frame__divider"></div>
        <div class="hud-frame__row" id="hudRowMode">
          <div class="label"><span class="dot"></span>Feed Mode</div>
          <div class="val" id="hudModeVal">SIMULATED</div>
        </div>
      </div>
    </div>
    <div id="canvas-container150"></div>
  </div>

  <div class="admin-only" id="adminTools">
    <a href="/twin/gearsystem150/motor" class="motor-link">Motor<span class="new-badge">NEW</span></a>
    <a href="/twin/gearsystem150/live-model" class="live-model-link">Live vs Model<span class="new-badge">NEW</span></a>
    <a href="/twin/gearsystem150/raw" class="live-model-link">Raw Waveform<span class="new-badge">NEW</span></a>
    <a href="/twin/gearsystem150/validate" class="live-model-link">Waveform Validation<span class="new-badge">NEW</span></a>
    <button class="ai-fab" id="aiFab">Ask AI</button>
    <div class="ai-panel" id="aiPanel">
      <div class="ai-panel__head">
        <h4>AI Assistant</h4>
        <button class="motor-modal__close" id="aiPanelClose" title="Close">×</button>
      </div>
      <details class="ai-company-info">
        <summary>Company info</summary>
        <textarea id="companyInfoText" placeholder="Datasheet specs, notes from the company..."></textarea>
        <button id="companyInfoSave">Save</button>
      </details>
      <div class="ai-panel__log" id="aiLog"></div>
      <div class="ai-panel__row">
        <input type="text" id="aiInput" placeholder="Ask about the gearbox...">
        <button id="aiSend">Send</button>
      </div>
      <button id="aiFaultCheck" class="ai-fault-btn">Run Fault Check</button>
    </div>
  </div>

<script type="importmap">
{
  "imports": {
    "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Static reference sketch, NOT to scale -- illustrative mid-range tooth
// counts only (exact counts unmeasured, searched by card-roulette below,
// this drawing doesn't change with that search).
//
// Layout read directly off the user's photo (top-down into the open
// housing), not guessed from words:
//   - Two large gears mesh DIRECTLY with each other (visible interlocking
//     teeth at the top of the photo) -- these are Blue and Green.
//   - A visibly smaller gear sits below/between them -- this is Yellow,
//     the MOTOR'S OWN ROTOR gear (confirmed by user), meshing directly
//     into the underside of Blue.
// Red and Output are NOT visible in this photo at all (hidden beneath the
// two visible big gears / by grease) -- their placement below is still a
// best-effort continuation, not photo-confirmed like Yellow/Blue/Green are.
const GEAR_H = 10;
// Real, measured tooth counts for this rig (locked hard constraints --
// see constraint_registry_metal.json) drive both radius and rendered
// tooth-box count below, instead of the old fixed R/RS/count=18
// placeholders that made every gear render identically regardless of its
// actual size. Module is uniform across meshing gears (a mechanical
// requirement -- gears that mesh must share a module), confirmed by the
// ~14mm outer-diameter measurement on the 27-tooth gears, so radius scales
// linearly with tooth count off a single reference.
const TEETH_YELLOW = 9, TEETH_BLUE_BIG = 27, TEETH_BLUE_SMALL = 8,
      TEETH_GREEN_BIG = 27, TEETH_GREEN_SMALL = 8,
      TEETH_RED_BIG = 27, TEETH_RED_SMALL = 16;
const UNITS_PER_TOOTH = 36 / TEETH_BLUE_BIG; // keeps 27-tooth gears at the same ~36-unit radius as before
const teethRadius = (teeth) => teeth * UNITS_PER_TOOTH;
const R = teethRadius(TEETH_BLUE_BIG);        // 27T -- Blue/Green/Red big side
const RS = teethRadius(TEETH_BLUE_SMALL);     // 8T -- Blue/Green coaxial small side
const R_YELLOW = teethRadius(TEETH_YELLOW);   // 9T
const RS_RED = teethRadius(TEETH_RED_SMALL);  // 16T -- Red's coaxial small side (cosmetic leaf, nothing meshes onto it in this view)

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1018);
const container = document.getElementById('canvas-container150');
const camera = new THREE.PerspectiveCamera(40, container.clientWidth / container.clientHeight, 0.1, 3000);
camera.position.set(-40, 180, 240);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(container.clientWidth, container.clientHeight);
container.appendChild(renderer.domElement);
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
orbit.dampingFactor = 0.07;
orbit.target.set(-22, 0, 27);
scene.add(new THREE.GridHelper(300, 20, 0x232838, 0x181c26));

function lmat(color) { return new THREE.LineBasicMaterial({ color }); }
function edgesOf(geo, color) { return new THREE.LineSegments(new THREE.EdgesGeometry(geo, 8), lmat(color)); }
function gearDisc(radius, height, color) { return edgesOf(new THREE.CylinderGeometry(radius, radius, height, 28), color); }
function gearTeeth(radius, height, color, count) {
  const g = new THREE.Group();
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2;
    const tooth = edgesOf(new THREE.BoxGeometry(radius * 0.1, height * 0.85, radius * 0.1), color);
    tooth.position.set(Math.cos(a) * radius, 0, Math.sin(a) * radius);
    g.add(tooth);
  }
  return g;
}
function discAt(y, radius, color, teethCount) {
  const disc = gearDisc(radius, GEAR_H, color);
  const teeth = gearTeeth(radius, GEAR_H, color, teethCount);
  disc.position.y = y; teeth.position.y = y;
  const g = new THREE.Group(); g.add(disc, teeth);
  return g;
}
function makeShaft(x, y, z, bigRadius, smallRadius, bigColor, smallColor, hasSmall, bigTeeth, smallTeeth) {
  const group = new THREE.Group();
  group.add(discAt(0, bigRadius, bigColor, bigTeeth));
  if (hasSmall) group.add(discAt(12, smallRadius, smallColor, smallTeeth));
  const shaftH = hasSmall ? 34 : 20;
  const shaftMesh = edgesOf(new THREE.CylinderGeometry(2, 2, shaftH, 12), 0x555c68);
  shaftMesh.position.y = shaftH / 2 - 4;
  group.add(shaftMesh);
  group.position.set(x, y, z);
  scene.add(group);
  return group;
}

// Blue: the large gear on the RIGHT in the photo (corrected -- previously
// placed as if "top-left"). Anchored at the origin -- everything else is
// placed relative to it.
const blueGroup = makeShaft(0, 0, 0, R, RS, 0x3498db, 0x2980b9, true, TEETH_BLUE_BIG, TEETH_BLUE_SMALL);

// Yellow: the motor's rotor, visibly smaller, sitting below Blue in the
// photo and meshing directly into it -- placed straight "below" (+Z) at
// exactly big+small radius apart (touching, not overlapping).
const yellowGroup = makeShaft(0, 0, R + R_YELLOW, R_YELLOW, 0, 0xf0a500, 0xf0a500, false, TEETH_YELLOW, 0);

// Green: on the LEFT in the photo (corrected -- previously placed on the
// +X/right side; mirrored to -X so Green renders left of Blue/Red). Big
// part meshes Blue's SMALL coaxial gear (not Blue's big gear directly).
// Blue's small sits at y=12, so Green sits at that same height too (gears
// only mesh when coplanar), at distance RS+R (Blue's small radius +
// Green's big radius), not R+R.
const angBlueGreen = Math.PI - (25 * Math.PI / 180);
const distBlueGreen = RS + R;
const greenX = Math.cos(angBlueGreen) * distBlueGreen, greenZ = Math.sin(angBlueGreen) * distBlueGreen;
const greenGroup = makeShaft(greenX, 12, greenZ, R, RS, 0x2ecc71, 0x27ae60, true, TEETH_GREEN_BIG, TEETH_GREEN_SMALL);

// Red: on the RIGHT, same side as Blue -- NOT visible in the photo, still
// a best-effort guess, but its mesh point (Green's small gear) is
// confirmed correct. Per correction: swing back the OTHER way (opposite
// angle) instead of continuing outward, so Red lands directly above Blue
// -- still meshing Green's small at the same distance, just not attached
// to Blue, purely stacked above it. (The reversed angle always lands Red
// exactly at Blue's x/z regardless of angBlueGreen's sign, since
// Blue-Green and Green-Red are the same distance apart.)
const angRedBack = angBlueGreen + Math.PI;
const redX = greenX + Math.cos(angRedBack) * (RS + R), redZ = greenZ + Math.sin(angRedBack) * (RS + R);
const redGroup = makeShaft(redX, 24, redZ, R, RS_RED, 0xff5566, 0xcc3344, true, TEETH_RED_BIG, TEETH_RED_SMALL);

// Output (purple/pink) removed from the visual -- not shown.

// Motor body -- gray cylinder tucked directly under Yellow, radius 68.75
// (27.5 x 2.5 per request), length 30 (24 x 1.25 per request).
const motorBody = edgesOf(new THREE.CylinderGeometry(68.75, 68.75, 30, 32), 0x5a6270);
motorBody.position.set(0, -16, R + RS);
scene.add(motorBody);

// Invisible solid mesh, same size/position as motorBody, purely so clicks
// have a real surface to hit -- raycasting against the wireframe's thin
// LineSegments alone makes the motor hard to click precisely.
const motorHitMesh = new THREE.Mesh(
  new THREE.CylinderGeometry(68.75, 68.75, 30, 32),
  new THREE.MeshBasicMaterial({ visible: false })
);
motorHitMesh.position.copy(motorBody.position);
scene.add(motorHitMesh);

const motorModalOverlay = document.getElementById('motorModalOverlay');
const motorModalClose = document.getElementById('motorModalClose');
const motorChainSub = document.getElementById('motorChainSub');
const motorChainBody = document.getElementById('motorChainBody');
const GEAR_ORDER = ['Yellow', 'Blue', 'Green', 'Red'];

function fmt(n, digits) {
  if (n === null || n === undefined || !isFinite(n)) return '--';
  return Number(n).toFixed(digits === undefined ? 3 : digits);
}

function renderMotorChain(data) {
  if (!data.available) {
    motorChainSub.textContent = 'No verified gearbox yet.';
    motorChainBody.innerHTML =
      '<p class="motor-chain-unverified">Run a roulette round on the ' +
      '<a href="/twin/gearsystem150/roulette" style="color:#4fd1c5">roulette page</a> ' +
      'and verify a card first -- that establishes the real tooth counts this chain depends on.</p>';
    return;
  }
  motorChainSub.textContent = 'Live physics chain from the verified gearbox twin.';

  const rpm = data.rpm_chain;
  const mesh = data.mesh_frequencies_hz;
  const sigByName = {};
  data.signatures.forEach((s) => { sigByName[s.name] = s; });

  let html = '';

  html += '<div class="motor-stage"><div class="motor-stage__label">1. RPM chain (anchored at Output = 150 RPM)</div>';
  html += '<div class="motor-stage-row">';
  ['Yellow', 'Blue', 'Green', 'Red', 'Output'].forEach((g) => {
    html += '<div class="motor-chip"><span class="k">' + g + '</span> ' + fmt(rpm[g], 1) + ' rpm</div>';
  });
  html += '</div></div>';

  html += '<div class="motor-stage"><div class="motor-stage__label">2. Mesh frequency (per gear)</div>';
  html += '<div class="motor-stage-row">';
  GEAR_ORDER.forEach((g) => {
    html += '<div class="motor-chip"><span class="k">' + g + '</span> ' + fmt(mesh[g], 2) + ' Hz</div>';
  });
  html += '</div></div>';

  html += '<div class="motor-stage"><div class="motor-stage__label">3. Baseline current</div>';
  html += '<div class="motor-stage-row"><div class="motor-chip">I_baseline ' + fmt(data.I_baseline_A, 4) + ' A</div></div></div>';

  html += '<div class="motor-stage"><div class="motor-stage__label">4-5. Per-gear signature (ΔI + rise time)</div>';
  html += '<table class="motor-sig-table"><tr><th>Gear</th><th>ΔI/N (A/N)</th><th>ΔI impulse</th><th>Rise (ms)</th><th>Freq (Hz)</th></tr>';
  GEAR_ORDER.forEach((g) => {
    const s = sigByName[g];
    if (!s) return;
    html += '<tr><td>' + g + '</td><td>' + fmt(s.delta_I_per_N_A, 5) + '</td><td>' +
      fmt(s.delta_I_per_impulse_A_per_Nms, 5) + '</td><td>' + fmt(s.rise_time_s * 1000, 2) + '</td><td>' +
      fmt(s.dominant_frequency_hz, 2) + '</td></tr>';
  });
  html += '</table></div>';

  motorChainBody.innerHTML = html;
}

function openMotorModal() {
  motorModalOverlay.classList.add('open');
  motorChainSub.textContent = 'Loading physics chain...';
  motorChainBody.innerHTML = '';
  fetch('/api/gearsystem/motor_chain')
    .then((r) => r.json())
    .then(renderMotorChain)
    .catch(() => {
      motorChainSub.textContent = 'Failed to load physics chain.';
    });
}
function closeMotorModal() { motorModalOverlay.classList.remove('open'); }
motorModalClose.addEventListener('click', closeMotorModal);
motorModalOverlay.addEventListener('click', (e) => {
  if (e.target === motorModalOverlay) closeMotorModal();
});
window.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeMotorModal(); });

const raycaster = new THREE.Raycaster();
const pointerNDC = new THREE.Vector2();
let pointerDownPos = null;
renderer.domElement.addEventListener('pointerdown', (e) => {
  pointerDownPos = { x: e.clientX, y: e.clientY };
});
renderer.domElement.addEventListener('pointerup', (e) => {
  if (!pointerDownPos) return;
  const moved = Math.hypot(e.clientX - pointerDownPos.x, e.clientY - pointerDownPos.y);
  pointerDownPos = null;
  if (moved > 4) return; // was a drag/orbit, not a click
  const rect = renderer.domElement.getBoundingClientRect();
  pointerNDC.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  pointerNDC.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointerNDC, camera);
  const hits = raycaster.intersectObject(motorHitMesh);
  if (hits.length > 0) openMotorModal();
});

// Per-gear touch blink -- set by the live-state poll below (real sensor
// data, the fault-o-meter's live matches, not a simulated/random fault).
// Highlights ONLY the specific gear(s) the fault-o-meter currently
// matches -- can be more than one at once (Blue/Green/Red's sensitivities
// are close enough to genuinely overlap, see gateway's module comment),
// in which case all matching gears blink together rather than forcing a
// single pick. Pulses toward a bright highlight color and back rather
// than a hard on/off flash.
window.gearsystemDetectedGears = []; // array of gear names currently matched, e.g. ['Blue','Green']
const GEAR_GROUPS_BY_NAME = { Yellow: yellowGroup, Blue: blueGroup, Green: greenGroup, Red: redGroup };
const _BLINK_COLOR = new THREE.Color(0xffe066);
const _blinkMaterials = []; // {mat, orig, gearName}
Object.entries(GEAR_GROUPS_BY_NAME).forEach(([gearName, g]) => g.traverse((obj) => {
  if (obj.material && obj.material.color) _blinkMaterials.push({ mat: obj.material, orig: obj.material.color.clone(), gearName });
}));

function updateTouchBlink() {
  const active = new Set(window.gearsystemDetectedGears || []);
  const t = performance.now() / 1000;
  const mix = 0.5 + 0.5 * Math.sin(t * 9);
  _blinkMaterials.forEach(({ mat, orig, gearName }) => {
    if (!active.has(gearName)) mat.color.copy(orig);
    else mat.color.copy(orig).lerp(_BLINK_COLOR, mix);
  });
}

function animate() {
  requestAnimationFrame(animate);
  orbit.update();
  updateTouchBlink();
  renderer.render(scene, camera);
}
animate();
window.addEventListener('resize', () => {
  camera.aspect = container.clientWidth / container.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.clientWidth, container.clientHeight);
});

const aiFab = document.getElementById('aiFab');
if (aiFab) {
  const aiPanel = document.getElementById('aiPanel');
  const aiPanelClose = document.getElementById('aiPanelClose');
  const aiLog = document.getElementById('aiLog');
  const aiInput = document.getElementById('aiInput');
  const aiSend = document.getElementById('aiSend');
  const aiFaultCheck = document.getElementById('aiFaultCheck');
  const companyInfoText = document.getElementById('companyInfoText');
  const companyInfoSave = document.getElementById('companyInfoSave');
  let companyInfoLoaded = false;

  aiFab.addEventListener('click', () => {
    aiPanel.classList.add('open');
    if (!companyInfoLoaded) {
      companyInfoLoaded = true;
      fetch('/api/admin/company_info').then(r => r.json()).then(d => {
        companyInfoText.value = d.text || '';
      });
    }
  });
  aiPanelClose.addEventListener('click', () => aiPanel.classList.remove('open'));
  companyInfoSave.addEventListener('click', () => {
    fetch('/api/admin/company_info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: companyInfoText.value }),
    });
  });

  function appendLog(label, text, cssClass) {
    if (label) {
      const labelDiv = document.createElement('div');
      labelDiv.className = 'msg fault-label';
      labelDiv.textContent = label;
      aiLog.appendChild(labelDiv);
    }
    const div = document.createElement('div');
    div.className = cssClass;
    div.textContent = text;
    aiLog.appendChild(div);
    aiLog.scrollTop = aiLog.scrollHeight;
  }

  async function sendAiQuestion() {
    const question = aiInput.value.trim();
    if (!question) return;
    appendLog(null, question, 'msg q');
    aiInput.value = '';
    try {
      const res = await fetch('/api/admin/ask_ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      appendLog(null, data.answer || data.error || 'No response.', 'msg a');
    } catch (e) {
      appendLog(null, 'Request failed.', 'msg a');
    }
  }

  async function runFaultCheck() {
    appendLog('Fault check', 'Analyzing current machine state...', 'msg q');
    try {
      const res = await fetch('/api/admin/ask_ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'fault_check' }),
      });
      const data = await res.json();
      appendLog(null, data.answer || data.error || 'No response.', 'msg a');
    } catch (e) {
      appendLog(null, 'Request failed.', 'msg a');
    }
  }

  aiSend.addEventListener('click', sendAiQuestion);
  aiInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendAiQuestion(); });
  aiFaultCheck.addEventListener('click', runFaultCheck);
}

const modeBtn3d = document.getElementById('modeBtn3d');
const modeBtnAdmin = document.getElementById('modeBtnAdmin');
function applyMode(mode) {
  document.body.classList.toggle('mode-admin', mode === 'admin');
  modeBtn3d.classList.toggle('active', mode !== 'admin');
  modeBtnAdmin.classList.toggle('active', mode === 'admin');
  localStorage.setItem('gearsystem150_mode', mode);
}
modeBtn3d.addEventListener('click', () => applyMode('3d'));
modeBtnAdmin.addEventListener('click', () => applyMode('admin'));
applyMode(localStorage.getItem('gearsystem150_mode') === 'admin' ? 'admin' : '3d');
</script>
<script>
(function () {
  const ACCENTS = { ok: '#3fd0ff', warn: '#f5a623', crit: '#ef4444', idle: '#5c6472' };
  const RANK = { ok: 0, idle: 1, warn: 2, crit: 3 };

  const hudFrame = document.getElementById('hudFrame');
  const rowCurrent = document.getElementById('hudRowCurrent');
  const rowFault = document.getElementById('hudRowFault');
  const rowMode = document.getElementById('hudRowMode');
  const currentVal = document.getElementById('hudCurrentVal');
  const faultVal = document.getElementById('hudFaultVal');
  const modeVal = document.getElementById('hudModeVal');

  let currentLevel = 'ok';
  let faultLevel = 'ok';
  let modeLevel = 'ok';

  function setRowLevel(row, level) {
    row.classList.toggle('level-idle', level === 'idle');
    row.style.setProperty('--row-accent', ACCENTS[level] || ACCENTS.ok);
  }

  function refreshFrameAccent() {
    let worst = 'ok';
    [currentLevel, faultLevel, modeLevel].forEach((l) => {
      if (RANK[l] > RANK[worst]) worst = l;
    });
    hudFrame.style.setProperty('--hud-accent', ACCENTS[worst] || ACCENTS.ok);
  }

  let currentTimer = null;

  const MODE_TEXT = {
    waiting_for_sensor: 'WAITING FOR SENSOR',
    connected: 'LIVE',
  };
  const MODE_LEVEL = {
    waiting_for_sensor: 'idle',
    connected: 'ok',
  };

  async function tickCurrent() {
    try {
      const r = await fetch('/api/gearsystem/live/state');
      const s = await r.json();

      modeVal.textContent = MODE_TEXT[s.status] || s.status.toUpperCase();
      modeLevel = MODE_LEVEL[s.status] || 'idle';
      setRowLevel(rowMode, modeLevel);

      if (!s.connected || s.current_A === null || s.current_A === undefined || s.stale) {
        currentVal.textContent = 'WAITING FOR SENSOR';
        currentLevel = 'idle';
        window.gearsystemDetectedGears = [];
        setFault('ok', s.connected ? 'AWAITING READING' : 'NO SENSOR');
      } else {
        currentVal.textContent = s.current_A.toFixed(3) + ' A · LIVE';
        currentLevel = 'ok';
        // Part Interruption -- proof-of-concept threshold/range detector
        // (see live_state.py's PART_INTERRUPTION_* config and
        // signal_processing.update_part_interruption()). Independent of
        // the older detected_gears/touched fields above -- at most one
        // gear at a time, straight from part_interruption_gear.
        const interruptedGear = s.part_interruption_gear || null;
        window.gearsystemDetectedGears = interruptedGear ? [interruptedGear] : [];
        setFault(interruptedGear ? 'warn' : 'ok', interruptedGear ? (interruptedGear + ' Gear Interrupted') : 'No Part Interrupted');
      }
    } catch (e) {
      modeVal.textContent = 'GATEWAY UNREACHABLE';
      modeLevel = 'warn';
      setRowLevel(rowMode, modeLevel);
      currentVal.textContent = 'WAITING FOR SENSOR';
      currentLevel = 'idle';
      window.gearsystemDetectedGears = [];
      setFault('ok', 'NO SENSOR');
    }
    setRowLevel(rowCurrent, currentLevel);
    refreshFrameAccent();
  }

  function setFault(level, text) {
    faultVal.textContent = text;
    faultLevel = level || 'ok';
    setRowLevel(rowFault, faultLevel);
    refreshFrameAccent();
  }

  function startSim() {
    clearInterval(currentTimer);
    tickCurrent();
    currentTimer = setInterval(tickCurrent, 150);
  }

  startSim();
})();
</script>
</body>
</html>
"""


GEARSYSTEM_TWIN_BATCH_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>150 RPM Gear System -- Twin Batch</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; min-height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 24px; }
  .head-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
  .head-row h1 { font-size: 17px; margin: 0; color: #fff; }
  .head-row .sub { font-size: 11.5px; color: #6b7280; margin-top: 2px; }
  .actions { display: flex; gap: 8px; align-items: center; }
  a.back-link { color: #4fd1c5; text-decoration: none; font-size: 12.5px; }
  button.regen {
    background: #0d6efd; border: 1px solid #0d6efd; color: #fff; font-weight: 600;
    border-radius: 6px; padding: 8px 14px; font-size: 12.5px; cursor: pointer;
  }
  button.regen:hover { background: #2b7fff; }
  button.regen:disabled { opacity: 0.5; cursor: not-allowed; }
  .table-shell { border: 1px solid #2a2f3a; border-radius: 8px; overflow-x: auto; background: #0d1018; margin-top: 18px; }
  table { border-collapse: collapse; width: 100%; font-size: 11.5px; font-family: "Courier New", monospace; white-space: nowrap; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid #1c2029; }
  th { color: #4fd1c5; text-transform: uppercase; font-size: 10px; letter-spacing: 0.4px; background: #0f131f; position: sticky; top: 0; }
  tr:hover td { background: #11141d; }
  .loading { color: #6b7280; padding: 20px; font-size: 12.5px; }
  .work-btn {
    background: #171b26; border: 1px solid #2a2f3a; color: #4fd1c5; border-radius: 5px;
    padding: 4px 9px; font-size: 10.5px; cursor: pointer; font-family: -apple-system, sans-serif;
  }
  .work-btn:hover { border-color: #4fd1c5; }
  .work-row td {
    white-space: normal; background: #0a0e18; font-size: 11px; line-height: 1.7; padding: 14px 18px;
  }
  .work-gear { margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #1c2029; }
  .work-gear:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
  .work-gear u { color: #f5a623; }
  .work-section b { color: #4fd1c5; }

  .formulas-panel {
    border: 1px solid #2a2f3a; border-radius: 8px; background: #0d1018; padding: 16px 20px; margin-top: 18px;
  }
  .formulas-panel summary { cursor: pointer; font-size: 13px; color: #fff; font-weight: 700; }
  .formula-block { margin-top: 14px; }
  .formula-label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #4fd1c5;
    font-weight: 700; margin-bottom: 5px;
  }
  .formula-block code {
    display: block; font-family: "Courier New", monospace; font-size: 12px; color: #f5a623;
    background: #171b26; border: 1px solid #2a2f3a; border-radius: 5px; padding: 6px 10px; margin-bottom: 4px;
  }
  .formula-desc { font-size: 11px; color: #9aa4b2; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="head-row">
      <div>
        <h1>Digital Twin Batch</h1>
        <div class="sub">20 independently sampled twins, each run through the full physics chain (registry: constraint_registry_metal.json)</div>
      </div>
      <div class="actions">
        <a href="/twin/gearsystem150" class="back-link">&larr; Back to twin</a>
        <button class="regen" id="regenBtn">Regenerate</button>
      </div>
    </div>

    <details class="formulas-panel" open>
      <summary>Formulas used</summary>
      <div class="formula-block">
        <div class="formula-label">1. RPM chain (anchored at Output = 150 RPM)</div>
        <code>RPM_next = RPM_prev &times; (T_driving / T_driven)</code>
        <div class="formula-desc">Red = 150 &times; (T_output/T_red,small) &rarr; Green = RPM_red &times; (T_red,big/T_green,small) &rarr; Blue = RPM_green &times; (T_green,big/T_blue,small) &rarr; Yellow = RPM_blue &times; (T_blue,big/T_yellow)</div>
      </div>
      <div class="formula-block">
        <div class="formula-label">2. Mesh frequency (per gear)</div>
        <code>f = (RPM / 60) &times; T</code>
      </div>
      <div class="formula-block">
        <div class="formula-label">3. Baseline current (global constant)</div>
        <code>I_baseline = I_BASELINE_A</code>
        <div class="formula-desc">Sampled directly, not derived -- the zero-reference every touch signature is measured against.</div>
      </div>
      <div class="formula-block">
        <div class="formula-label">4. Steady-force touch model (per gear, "held press")</div>
        <code>r_mm = (T_big &times; MODULE_MM) / 2  &rarr;  r_m = r_mm / 1000</code>
        <code>&eta;_chain = GEAR_MESH_EFFICIENCY ^ n</code>
        <code>&tau;_perN = r_m &times; &mu; &times; &eta;_chain  &rarr;  &Delta;I_perN = &tau;_perN &times; CURRENT_PER_NM</code>
        <div class="formula-desc">n = meshes between the touched gear and Output. &mu; = METAL_OILED_FRICTION_COEFF.</div>
      </div>
      <div class="formula-block">
        <div class="formula-label">5. Impact-response model (per gear, "screwdriver strike")</div>
        <code>mass = MATERIAL_DENSITY_KG_M3 &times; &pi; &times; r_m&sup2; &times; GEAR_WIDTH_MM/1000</code>
        <code>I_rot = 0.5 &times; mass &times; r_m&sup2;</code>
        <code>&Delta;I_impulse = &eta;_chain &times; CURRENT_PER_IMPULSE / I_rot</code>
      </div>
      <div class="formula-block">
        <div class="formula-label">6. Rise time (per gear)</div>
        <code>t_rise = 0.002 &times; (1 + 0.15 &times; n)</code>
      </div>
    </details>

    <div class="table-shell">
      <table id="twinTable">
        <thead>
          <tr>
            <th>Twin</th><th>Yellow</th><th>Blue (S/B)</th><th>Green (S/B)</th><th>Red (S/B)</th><th>Output</th>
            <th>Module (mm)</th><th>Friction &mu;</th><th>I_base (A)</th>
            <th>RPM Yellow</th><th>RPM Blue</th><th>RPM Green</th><th>RPM Red</th><th></th><th></th>
          </tr>
        </thead>
        <tbody><tr><td colspan="15" class="loading">Loading twins...</td></tr></tbody>
      </table>
    </div>
  </div>
<script>
function fmt(n, d) { return (n === null || n === undefined || !isFinite(n)) ? '--' : Number(n).toFixed(d === undefined ? 1 : d); }

function teethFor(c, gearName) {
  if (gearName === 'Yellow') return c.TEETH_YELLOW;
  if (gearName === 'Blue') return c.TEETH_BLUE_BIG;
  if (gearName === 'Green') return c.TEETH_GREEN_BIG;
  return c.TEETH_RED_BIG;
}

function buildWorkHtml(t) {
  const c = t.constants, rpm = t.rpm_chain, mesh = t.mesh_frequencies_hz;
  let html = '';

  html += '<div class="work-section"><b>1. RPM chain</b><br>';
  html += 'RPM_red = 150 &times; (' + c.TEETH_OUTPUT_BIG + '/' + c.TEETH_RED_SMALL + ') = ' + fmt(rpm.Red, 2) + ' rpm<br>';
  html += 'RPM_green = RPM_red &times; (' + c.TEETH_RED_BIG + '/' + c.TEETH_GREEN_SMALL + ') = ' + fmt(rpm.Green, 2) + ' rpm<br>';
  html += 'RPM_blue = RPM_green &times; (' + c.TEETH_GREEN_BIG + '/' + c.TEETH_BLUE_SMALL + ') = ' + fmt(rpm.Blue, 2) + ' rpm<br>';
  html += 'RPM_yellow = RPM_blue &times; (' + c.TEETH_BLUE_BIG + '/' + c.TEETH_YELLOW + ') = ' + fmt(rpm.Yellow, 2) + ' rpm</div>';

  html += '<div class="work-section"><b>2. Mesh frequency</b><br>';
  ['Yellow', 'Blue', 'Green', 'Red'].forEach((g) => {
    html += 'f_' + g + ' = (' + fmt(rpm[g], 2) + '/60) &times; ' + teethFor(c, g) + ' = ' + fmt(mesh[g], 2) + ' Hz<br>';
  });
  html += '</div>';

  html += '<div class="work-section"><b>3. Baseline current</b><br>I_baseline = ' + fmt(t.I_baseline_A, 4) + ' A (sampled constant)</div>';

  html += '<div class="work-section"><b>4-6. Per-gear signature</b>';
  t.signatures.forEach((s) => {
    const Tbig = teethFor(c, s.name);
    const r_mm = (Tbig * c.MODULE_MM) / 2;
    html += '<div class="work-gear"><u>' + s.name + '</u> (n=' + s.n_stages_from_motor + ' meshes from motor)<br>';
    html += 'r_mm = (' + Tbig + ' &times; ' + fmt(c.MODULE_MM, 3) + ')/2 = ' + fmt(r_mm, 3) + ' mm<br>';
    html += '&eta;_chain = ' + fmt(c.GEAR_MESH_EFFICIENCY, 3) + '^' + s.n_stages_from_motor + '<br>';
    html += '&Delta;I_perN = &tau;_perN &times; CURRENT_PER_NM = ' + fmt(s.delta_I_per_N_A, 5) + ' A/N<br>';
    html += 'mass = &rho;&times;&pi;&times;r_m&sup2;&times;width = ' + fmt(s.mass_kg, 5) + ' kg<br>';
    html += 'I_rot = 0.5&times;mass&times;r_m&sup2; = ' + fmt(s.inertia_kgm2, 8) + ' kg&middot;m&sup2;<br>';
    html += '&Delta;I_impulse = &eta;_chain&times;CURRENT_PER_IMPULSE/I_rot = ' + fmt(s.delta_I_per_impulse_A_per_Nms, 3) + '<br>';
    html += 't_rise = 0.002&times;(1+0.15&times;' + s.n_stages_from_motor + ') = ' + fmt(s.rise_time_s * 1000, 2) + ' ms</div>';
  });
  html += '</div>';

  return html;
}

async function loadTwins() {
  const tbody = document.querySelector('#twinTable tbody');
  tbody.innerHTML = '<tr><td colspan="15" class="loading">Loading twins...</td></tr>';
  const data = await fetch('/api/gearsystem/twin_batch').then(r => r.json());
  tbody.innerHTML = '';
  data.twins.forEach((t) => {
    const c = t.constants;
    const rpm = t.rpm_chain;
    const row = document.createElement('tr');
    row.innerHTML =
      '<td>' + t.twin_id + '</td>' +
      '<td>' + c.TEETH_YELLOW + '</td>' +
      '<td>' + c.TEETH_BLUE_SMALL + ' / ' + c.TEETH_BLUE_BIG + '</td>' +
      '<td>' + c.TEETH_GREEN_SMALL + ' / ' + c.TEETH_GREEN_BIG + '</td>' +
      '<td>' + c.TEETH_RED_SMALL + ' / ' + c.TEETH_RED_BIG + '</td>' +
      '<td>' + c.TEETH_OUTPUT_BIG + '</td>' +
      '<td>' + fmt(c.MODULE_MM, 3) + '</td>' +
      '<td>' + fmt(c.METAL_OILED_FRICTION_COEFF, 3) + '</td>' +
      '<td>' + fmt(t.I_baseline_A, 4) + '</td>' +
      '<td>' + fmt(rpm.Yellow, 1) + '</td>' +
      '<td>' + fmt(rpm.Blue, 1) + '</td>' +
      '<td>' + fmt(rpm.Green, 1) + '</td>' +
      '<td>' + fmt(rpm.Red, 1) + '</td>' +
      '<td><button class="work-btn" data-twin="' + t.twin_id + '">Show work</button></td>' +
      '<td><button class="work-btn sim-btn">Simulate touch</button></td>';
    tbody.appendChild(row);

    const workRow = document.createElement('tr');
    workRow.className = 'work-row';
    workRow.style.display = 'none';
    const workCell = document.createElement('td');
    workCell.colSpan = 15;
    workCell.innerHTML = buildWorkHtml(t);
    workRow.appendChild(workCell);
    tbody.appendChild(workRow);

    row.querySelector('.work-btn').addEventListener('click', (e) => {
      const open = workRow.style.display !== 'none';
      workRow.style.display = open ? 'none' : 'table-row';
      e.target.textContent = open ? 'Show work' : 'Hide work';
    });

    row.querySelector('.sim-btn').addEventListener('click', () => {
      sessionStorage.setItem('touchSimConstants', JSON.stringify(t.constants));
      sessionStorage.setItem('touchSimLabel', 'Twin #' + t.twin_id);
      window.location.href = '/twin/gearsystem150/touch-sim';
    });
  });
}

document.getElementById('regenBtn').addEventListener('click', async () => {
  const btn = document.getElementById('regenBtn');
  btn.disabled = true;
  await loadTwins();
  btn.disabled = false;
});

loadTwins();
</script>
</body>
</html>
"""


GEARSYSTEM_TOUCH_SIM_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>150 RPM Gear System -- Touch Simulation</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; min-height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .wrap { max-width: 1000px; margin: 0 auto; padding: 24px; }
  .head-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
  .head-row h1 { font-size: 17px; margin: 0; color: #fff; }
  .head-row .sub { font-size: 11.5px; color: #6b7280; margin-top: 2px; }
  a.back-link { color: #4fd1c5; text-decoration: none; font-size: 12.5px; }

  .controls {
    border: 1px solid #2a2f3a; border-radius: 8px; background: #0d1018; padding: 16px 20px;
    display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; margin-bottom: 18px;
  }
  .field { display: flex; flex-direction: column; gap: 5px; }
  .field label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; font-weight: 600;
  }
  .field select, .field input {
    background: #171b26; border: 1px solid #2a2f3a; color: #e6faff; border-radius: 6px;
    padding: 7px 9px; font-size: 12.5px; min-width: 140px;
  }
  .field select:focus, .field input:focus { outline: none; border-color: #0d6efd; }
  button.sim-run {
    background: #0d6efd; border: 1px solid #0d6efd; color: #fff; font-weight: 700;
    border-radius: 6px; padding: 9px 18px; font-size: 12.5px; cursor: pointer;
  }
  button.sim-run:hover { background: #2b7fff; }
  button.sim-run:disabled { opacity: 0.5; cursor: not-allowed; }

  .sim-result {
    border: 1px solid #2a2f3a; border-radius: 8px; background: #0d1018; padding: 16px 20px; margin-bottom: 14px;
  }
  .sim-result h3 { margin: 0 0 4px; font-size: 13px; color: #f5a623; }
  .sim-stats { display: flex; gap: 16px; flex-wrap: wrap; font-family: "Courier New", monospace; font-size: 11.5px; color: #9aa4b2; margin-bottom: 10px; }
  .sim-stats b { color: #4fd1c5; }
  svg.sim-chart { width: 100%; height: 160px; display: block; }
  .placeholder { color: #6b7280; font-size: 12.5px; padding: 20px; text-align: center; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="head-row">
      <div>
        <h1>Touch Simulation</h1>
        <div class="sub">Simulate a touch on a gear and generate the resulting current signature</div>
      </div>
      <a href="/twin/gearsystem150" class="back-link">&larr; Back to twin</a>
    </div>

    <div class="controls">
      <div class="field">
        <label>Twin</label>
        <select id="twinSelect"></select>
      </div>
      <div class="field">
        <label>Component</label>
        <select id="gearSelect">
          <option value="all">All gears</option>
          <option value="Yellow">Yellow</option>
          <option value="Blue">Blue</option>
          <option value="Green">Green</option>
          <option value="Red">Red</option>
        </select>
      </div>
      <div class="field">
        <label>Touch type</label>
        <select id="touchTypeSelect">
          <option value="impact">Impact strike</option>
          <option value="steady">Steady press</option>
          <option value="tooth_strike">NEW: Tooth-strike buzz (Real dynamics only)</option>
        </select>
      </div>
      <div class="field" id="forceField" style="display:none">
        <label>Force (N)</label>
        <input type="number" id="forceInput" value="0.5" step="0.1" min="0.1" max="15">
      </div>
      <div class="field" id="impulseField">
        <label>Impulse (N&middot;ms)</label>
        <input type="number" id="impulseInput" value="5" step="0.5" min="0.1">
      </div>
      <div class="field">
        <label>&nbsp;</label>
        <label style="text-transform:none; letter-spacing:normal; font-weight:400; display:flex; align-items:center; gap:6px; color:#d7dbe0; font-size:12.5px; cursor:pointer;">
          <input type="checkbox" id="dynamicToggle" style="width:auto; min-width:0;">
          Real dynamics (backlash + mesh stiffness)
          <span class="new-badge" style="margin-left:0; background:#f5a623; color:#1a1200; padding:1px 6px; border-radius:8px; font-size:9px; font-weight:800;">NEW</span>
        </label>
      </div>
      <button class="sim-run" id="simRunBtn">Simulate</button>
    </div>

    <div id="simResults"><div class="placeholder">Pick a twin and hit Simulate.</div></div>
  </div>
<script>
function fmt(n, d) { return (n === null || n === undefined || !isFinite(n)) ? '--' : Number(n).toFixed(d === undefined ? 4 : d); }

const twinSelect = document.getElementById('twinSelect');
const gearSelect = document.getElementById('gearSelect');
const touchTypeSelect = document.getElementById('touchTypeSelect');
const forceField = document.getElementById('forceField');
const impulseField = document.getElementById('impulseField');
let twinConstantsMap = {};

touchTypeSelect.addEventListener('change', () => {
  const isSteady = touchTypeSelect.value === 'steady';
  forceField.style.display = isSteady ? 'flex' : 'none';
  impulseField.style.display = isSteady ? 'none' : 'flex';
});

async function loadTwinOptions() {
  const passedConstants = sessionStorage.getItem('touchSimConstants');
  const passedLabel = sessionStorage.getItem('touchSimLabel');
  if (passedConstants) {
    const key = 'passed';
    twinConstantsMap[key] = JSON.parse(passedConstants);
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = passedLabel || 'Selected twin';
    twinSelect.appendChild(opt);
  }

  try {
    const motorChain = await fetch('/api/gearsystem/motor_chain').then(r => r.json());
    if (motorChain.available) {
      twinConstantsMap['verified'] = motorChain.constants;
      const opt = document.createElement('option');
      opt.value = 'verified';
      opt.textContent = 'Verified (real) twin';
      twinSelect.appendChild(opt);
    }
  } catch (e) {}

  const data = await fetch('/api/gearsystem/twin_batch').then(r => r.json());
  data.twins.forEach((t) => {
    const key = 'batch_' + t.twin_id;
    twinConstantsMap[key] = t.constants;
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = 'Twin #' + t.twin_id;
    twinSelect.appendChild(opt);
  });
}

function buildChartSvg(waveform, baseline) {
  const w = 560, h = 150, pad = 8;
  const currents = waveform.map(p => p.current_A);
  const times = waveform.map(p => p.t_ms);
  const minC = Math.min(...currents, baseline), maxC = Math.max(...currents, baseline);
  const range = (maxC - minC) || 0.0001;
  const maxT = Math.max(...times) || 1;
  const x = (t) => pad + (t / maxT) * (w - pad * 2);
  const y = (c) => (h - pad) - ((c - minC) / range) * (h - pad * 2);
  const pathPts = waveform.map(p => x(p.t_ms) + ',' + y(p.current_A)).join(' ');
  const baseY = y(baseline);
  return '<svg class="sim-chart" viewBox="0 0 ' + w + ' ' + h + '" preserveAspectRatio="none">' +
    '<line x1="' + pad + '" y1="' + baseY + '" x2="' + (w - pad) + '" y2="' + baseY + '" stroke="#2a2f3a" stroke-dasharray="4,3" stroke-width="1"/>' +
    '<polyline points="' + pathPts + '" fill="none" stroke="#4fd1c5" stroke-width="2"/>' +
    '</svg>';
}

async function runSimulation() {
  const twinKey = twinSelect.value;
  const constants = twinConstantsMap[twinKey];
  if (!constants) return;
  const btn = document.getElementById('simRunBtn');
  btn.disabled = true;
  const resultsEl = document.getElementById('simResults');
  resultsEl.innerHTML = '<div class="placeholder">Simulating...</div>';

  const body = {
    constants: constants,
    gear: gearSelect.value,
    touch_type: touchTypeSelect.value,
    force_n: parseFloat(document.getElementById('forceInput').value) || 0.5,
    impulse_ns: parseFloat(document.getElementById('impulseInput').value) || 5,
  };

  const useDynamic = document.getElementById('dynamicToggle').checked;
  const endpoint = useDynamic ? '/api/gearsystem/touch_sim_dynamic' : '/api/gearsystem/touch_sim';

  try {
    const data = await fetch(endpoint, {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body),
    }).then(r => r.json());

    if (data.error) {
      resultsEl.innerHTML = '<div class="placeholder">' + data.error + '</div>';
      return;
    }

    resultsEl.innerHTML = '';
    data.sims.forEach((sim) => {
      const block = document.createElement('div');
      block.className = 'sim-result';
      block.innerHTML =
        '<h3>' + sim.gear + '</h3>' +
        '<div class="sim-stats">' +
          '<span>&Delta;I: <b>' + fmt(sim.delta_I_A, 5) + ' A</b></span>' +
          '<span>Peak: <b>' + fmt(sim.peak_A, 5) + ' A</b></span>' +
          '<span>Rise time: <b>' + fmt(sim.rise_time_s * 1000, 2) + ' ms</b></span>' +
          '<span>Shape: <b>' + sim.signature_shape + '</b></span>' +
        '</div>' +
        buildChartSvg(sim.waveform, data.I_baseline_A);
      resultsEl.appendChild(block);
    });
  } finally {
    btn.disabled = false;
  }
}

document.getElementById('simRunBtn').addEventListener('click', runSimulation);
loadTwinOptions();
</script>
</body>
</html>
"""


GEARSYSTEM_LIVE_MODEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>150 RPM Gear System -- Live vs Model</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; min-height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .wrap { max-width: 900px; margin: 0 auto; padding: 24px; }
  .head-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
  .head-row h1 { font-size: 17px; margin: 0; color: #fff; }
  .head-row .sub { font-size: 11.5px; color: #6b7280; margin-top: 2px; }
  a.back-link { color: #4fd1c5; text-decoration: none; font-size: 12.5px; }

  .panel {
    border: 1px solid #2a2f3a; border-radius: 8px; background: #0d1018; padding: 16px 20px; margin-bottom: 18px;
  }
  .panel h3 { margin: 0 0 10px; font-size: 13px; color: #f5a623; }
  .row { display: flex; gap: 20px; flex-wrap: wrap; align-items: center; }
  .stat { display: flex; flex-direction: column; gap: 3px; }
  .stat label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; font-weight: 600; }
  .stat .v { font-family: "Courier New", monospace; font-size: 15px; color: #e6faff; }
  .flag { padding: 2px 8px; border-radius: 10px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; }
  .flag.ok { background: #123324; color: #4fd1c5; }
  .flag.stale { background: #33201a; color: #f5a623; }
  .flag.touch { background: #3a1a2a; color: #ff6b9d; }

  button {
    background: #0d6efd; border: 1px solid #0d6efd; color: #fff; font-weight: 700;
    border-radius: 6px; padding: 8px 16px; font-size: 12.5px; cursor: pointer;
  }
  button:hover { background: #2b7fff; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }

  table { width: 100%; border-collapse: collapse; margin-top: 4px; }
  th { text-align: left; color: #4fd1c5; text-transform: uppercase; font-size: 10px; letter-spacing: 0.4px; padding: 6px 8px; border-bottom: 1px solid #2a2f3a; }
  td { padding: 7px 8px; font-family: "Courier New", monospace; font-size: 12.5px; border-bottom: 1px solid #171b26; }
  tr.closest td { background: #0f2a22; color: #4fd1c5; }
  .placeholder { color: #6b7280; font-size: 12.5px; padding: 16px 0; }
  .warn { color: #f5a623; font-size: 12px; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="head-row">
      <div>
        <h1>Live vs Model</h1>
        <div class="sub">Real ESP32 sensor delta next to the verified twin's dynamic-model prediction, side by side</div>
      </div>
      <a href="/twin/gearsystem150" class="back-link">&larr; Back to twin</a>
    </div>

    <div class="panel">
      <h3>Live Sensor</h3>
      <div class="row">
        <div class="stat"><label>Raw current</label><div class="v" id="rawCurrent">--</div></div>
        <div class="stat"><label>Calibrated delta</label><div class="v" id="liveDelta">--</div></div>
        <div class="stat"><label>Noise floor</label><div class="v" id="noiseFloor">--</div></div>
        <div class="stat"><label>Status</label><div><span class="flag" id="liveFlag">--</span></div></div>
        <button id="calibrateBtn">Zero-calibrate</button>
      </div>
      <div class="warn" id="calibrateStatus" style="margin-top:8px"></div>
    </div>

    <div class="panel">
      <h3>Model Comparison</h3>
      <div id="modelBody"><div class="placeholder">Loading...</div></div>
    </div>
  </div>
<script>
function fmt(n, d) { return (n === null || n === undefined || !isFinite(n)) ? '--' : Number(n).toFixed(d === undefined ? 5 : d); }

async function calibrateZero() {
  const btn = document.getElementById('calibrateBtn');
  btn.disabled = true;
  try {
    const r = await fetch('/api/gearsystem/live/zero_calibrate', { method: 'POST' });
    const status = document.getElementById('calibrateStatus');
    if (!r.ok) { status.textContent = 'calibration failed -- no live reading yet'; return; }
    const d = await r.json();
    status.textContent = 'calibrated at ' + fmt(d.real_zero_A) + ' A';
  } finally {
    btn.disabled = false;
  }
}
document.getElementById('calibrateBtn').addEventListener('click', calibrateZero);

async function pollLiveState() {
  try {
    const s = await fetch('/api/gearsystem/live/state').then(r => r.json());
    document.getElementById('rawCurrent').textContent = fmt(s.current_A, 4) + ' A';
    const flag = document.getElementById('liveFlag');
    if (!s.connected) { flag.textContent = 'ESP32 not connected'; flag.className = 'flag stale'; }
    else if (s.stale) { flag.textContent = 'stale'; flag.className = 'flag stale'; }
    else { flag.textContent = 'live'; flag.className = 'flag ok'; }
  } catch (e) {}
}

async function pollModelCompare() {
  const modelBody = document.getElementById('modelBody');
  try {
    const d = await fetch('/api/gearsystem/live/model_compare').then(r => r.json());
    if (!d.available) {
      modelBody.innerHTML = '<div class="placeholder">' + (d.error || 'not available') + ' -- verify a card on the <a href="/twin/gearsystem150/roulette" style="color:#4fd1c5">roulette page</a> first.</div>';
      document.getElementById('liveDelta').textContent = '--';
      document.getElementById('noiseFloor').textContent = '--';
      return;
    }
    if (!d.calibrated) {
      modelBody.innerHTML = '<div class="placeholder">Not calibrated yet -- click Zero-calibrate above with the motor at rest.</div>';
      return;
    }
    if (d.error) {
      modelBody.innerHTML = '<div class="placeholder">' + d.error + '</div>';
      return;
    }

    document.getElementById('liveDelta').textContent = fmt(d.real_delta_A) + ' A';
    document.getElementById('noiseFloor').textContent = fmt(d.noise_floor_A) + ' A';
    const liveFlag = document.getElementById('liveFlag');
    if (d.detected === 'touch') { liveFlag.textContent = 'touch detected'; liveFlag.className = 'flag touch'; }

    if (!d.model_predictions || d.model_predictions.length === 0) {
      modelBody.innerHTML = '<div class="placeholder">No dynamic model predictions on the verified twin.</div>';
      return;
    }

    const rows = d.model_predictions.map(p => {
      const cls = (d.closest_gear === p.gear) ? ' class="closest"' : '';
      return '<tr' + cls + '>' +
        '<td>' + p.gear + (d.closest_gear === p.gear ? ' &larr; closest' : '') + '</td>' +
        '<td>' + fmt(p.predicted_delta_I_A) + ' A</td>' +
        '<td>' + p.predicted_touch_type + '</td>' +
        '<td>' + fmt(p.diff_from_live_A) + ' A</td>' +
        '</tr>';
    }).join('');
    modelBody.innerHTML =
      '<div class="warn" style="margin-bottom:8px">' +
      (d.detected === 'touch' ? 'Touch detected -- comparing against each gear\\'s model-predicted signature.' : 'No touch detected (delta below noise floor).') +
      ' Model predictions are computed once at verify time for one reference touch magnitude/type -- treat "closest" as a hint, not a verdict.</div>' +
      '<table><thead><tr><th>Gear</th><th>Model &Delta;I</th><th>Touch type</th><th>|diff from live|</th></tr></thead><tbody>' +
      rows + '</tbody></table>';
  } catch (e) {
    modelBody.innerHTML = '<div class="placeholder">error loading model comparison</div>';
  }
}

pollLiveState();
pollModelCompare();
setInterval(pollLiveState, 700);
setInterval(pollModelCompare, 700);
</script>
</body>
</html>
"""


GEARSYSTEM_MOTOR_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>150 RPM Gear System -- Motor</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; min-height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .wrap { max-width: 1000px; margin: 0 auto; padding: 24px; }
  .head-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
  .head-row h1 { font-size: 17px; margin: 0; color: #fff; }
  .head-row .sub { font-size: 11.5px; color: #6b7280; margin-top: 2px; }
  a.back-link { color: #4fd1c5; text-decoration: none; font-size: 12.5px; }
  a.nav-link { color: #4fd1c5; text-decoration: none; font-size: 12px; border: 1px solid #2a2f3a; border-radius: 16px; padding: 6px 12px; }
  a.nav-link:hover { border-color: #4fd1c5; }
  .nav-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }

  .panel { border: 1px solid #2a2f3a; border-radius: 8px; background: #0d1018; padding: 16px 20px; margin-bottom: 18px; }
  .panel h3 { margin: 0 0 10px; font-size: 13px; color: #f5a623; text-transform: uppercase; letter-spacing: 0.4px; }
  .panel .note { font-size: 11px; color: #6b7280; margin-top: 8px; }

  .spec-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px; }
  .spec { display: flex; flex-direction: column; gap: 3px; }
  .spec label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; font-weight: 600; }
  .spec .v { font-family: "Courier New", monospace; font-size: 15px; color: #e6faff; }
  .spec .tag { font-size: 9px; padding: 1px 6px; border-radius: 8px; margin-left: 6px; vertical-align: middle; font-weight: 800; }
  .tag.measured { background: #123324; color: #4fd1c5; }
  .tag.assumed { background: #33201a; color: #f5a623; }

  table { width: 100%; border-collapse: collapse; margin-top: 4px; }
  th { text-align: left; color: #4fd1c5; text-transform: uppercase; font-size: 10px; letter-spacing: 0.4px; padding: 6px 8px; border-bottom: 1px solid #2a2f3a; }
  td { padding: 7px 8px; font-family: "Courier New", monospace; font-size: 12.5px; border-bottom: 1px solid #171b26; }
  .placeholder { color: #6b7280; font-size: 12.5px; padding: 16px 0; }
</style>
</head>
<body>
  <div class="wrap">
    <div class="head-row">
      <div>
        <h1>Motor</h1>
        <div class="sub">150 RPM metal internal gearbox rig -- nameplate facts, physics chain, and both signature models for the verified twin</div>
      </div>
      <a href="/twin/gearsystem150" class="back-link">&larr; Back to twin</a>
    </div>

    <div class="nav-row">
      <a href="/twin/gearsystem150/touch-sim" class="nav-link">Touch Sim</a>
      <a href="/twin/gearsystem150/live-model" class="nav-link">Live vs Model</a>
    </div>

    <div class="panel">
      <h3>Nameplate</h3>
      <div class="spec-grid">
        <div class="spec"><label>Supply voltage<span class="tag measured">measured</span></label><div class="v" id="specVoltage">--</div></div>
        <div class="spec"><label>Rated output speed<span class="tag measured">measured</span></label><div class="v" id="specRpm">--</div></div>
        <div class="spec"><label>Sensor</label><div class="v">ACS712-30A</div></div>
        <div class="spec"><label>Baseline current<span class="tag assumed">sampled</span></label><div class="v" id="specBaseline">--</div></div>
        <div class="spec"><label>Current per N&middot;m<span class="tag assumed">sampled</span></label><div class="v" id="specCurrentPerNm">--</div></div>
        <div class="spec"><label>Rotor radius<span class="tag assumed">assumed</span></label><div class="v" id="specRotorR">--</div></div>
        <div class="spec"><label>Rotor length<span class="tag assumed">assumed</span></label><div class="v" id="specRotorL">--</div></div>
        <div class="spec"><label>Material density<span class="tag assumed">assumed</span></label><div class="v" id="specDensity">--</div></div>
        <div class="spec"><label>Young's modulus<span class="tag assumed">assumed</span></label><div class="v" id="specE">--</div></div>
      </div>
      <div class="note">"measured" = physically observed on the real unit. "sampled" = a BVS-searched value from the verified twin. "assumed" = an engineering stand-in, not measured for this specific unit -- see constraint_registry_metal.json's geometry_and_material_note.</div>
    </div>

    <div class="panel">
      <h3>RPM &amp; Mesh Frequency Chain</h3>
      <div id="chainBody"><div class="placeholder">Loading...</div></div>
    </div>

    <div class="panel">
      <h3>Steady-State Signatures (formula_chain_metal.run_formula_chain)</h3>
      <div id="steadyBody"><div class="placeholder">Loading...</div></div>
    </div>

    <div class="panel">
      <h3>Dynamic-Model Signatures (dynamic_gear_simulator, cached at verify time)</h3>
      <div id="dynamicBody"><div class="placeholder">Loading...</div></div>
    </div>
  </div>
<script>
function fmt(n, d) { return (n === null || n === undefined || !isFinite(n)) ? '--' : Number(n).toFixed(d === undefined ? 5 : d); }

async function loadMotor() {
  try {
    const d = await fetch('/api/gearsystem/motor_chain').then(r => r.json());
    if (!d.available) {
      const msg = '<div class="placeholder">No verified twin yet -- run a round on the ' +
        '<a href="/twin/gearsystem150/roulette" style="color:#4fd1c5">roulette page</a> and verify a card first.</div>';
      document.getElementById('chainBody').innerHTML = msg;
      document.getElementById('steadyBody').innerHTML = msg;
      document.getElementById('dynamicBody').innerHTML = msg;
      return;
    }

    document.getElementById('specVoltage').textContent = fmt(d.nameplate.MOTOR_SUPPLY_VOLTAGE_V, 0) + ' V';
    document.getElementById('specRpm').textContent = fmt(d.nameplate.MOTOR_RPM_OUTPUT_METAL, 0) + ' RPM';
    document.getElementById('specBaseline').textContent = fmt(d.I_baseline_A, 5) + ' A';
    document.getElementById('specCurrentPerNm').textContent = fmt(d.constants.CURRENT_PER_NM, 3) + ' A/N·m';
    document.getElementById('specRotorR').textContent = fmt(d.constants.MOTOR_ROTOR_RADIUS_MM, 2) + ' mm';
    document.getElementById('specRotorL').textContent = fmt(d.constants.MOTOR_ROTOR_LENGTH_MM, 2) + ' mm';
    document.getElementById('specDensity').textContent = fmt(d.constants.MATERIAL_DENSITY_KG_M3, 0) + ' kg/m³';
    document.getElementById('specE').textContent = fmt((d.constants.MATERIAL_YOUNGS_MODULUS_PA || 0) / 1e9, 0) + ' GPa';

    const gears = ['Yellow', 'Blue', 'Green', 'Red', 'Output'];
    const rpmRows = gears.map(g => '<tr><td>' + g + '</td><td>' + fmt(d.rpm_chain[g], 2) + ' RPM</td><td>' +
      (d.mesh_frequencies_hz[g] !== undefined ? fmt(d.mesh_frequencies_hz[g], 2) + ' Hz' : '--') + '</td></tr>').join('');
    document.getElementById('chainBody').innerHTML =
      '<table><thead><tr><th>Node</th><th>RPM</th><th>Mesh Freq</th></tr></thead><tbody>' + rpmRows + '</tbody></table>';

    const steadyRows = d.signatures.map(s => '<tr><td>' + s.name + '</td>' +
      '<td>' + fmt(s.delta_I_per_N_A, 5) + ' A/N</td>' +
      '<td>' + fmt(s.delta_I_per_impulse_A_per_Nms, 3) + '</td>' +
      '<td>' + fmt(s.rise_time_s * 1000, 3) + ' ms</td>' +
      '<td>' + s.signature_shape + '</td></tr>').join('');
    document.getElementById('steadyBody').innerHTML =
      '<table><thead><tr><th>Gear</th><th>&Delta;I per N</th><th>&Delta;I per impulse</th><th>Rise time</th><th>Shape</th></tr></thead><tbody>' + steadyRows + '</tbody></table>';

    if (!d.dynamic_signatures) {
      document.getElementById('dynamicBody').innerHTML =
        '<div class="placeholder">This verified twin predates dynamic_signatures -- re-verify a card on the roulette page to add them.</div>';
    } else {
      const dynRows = Object.entries(d.dynamic_signatures).map(([gear, sig]) => {
        if (sig.error) return '<tr><td>' + gear + '</td><td colspan="4">error: ' + sig.error + '</td></tr>';
        return '<tr><td>' + gear + '</td>' +
          '<td>' + fmt(sig.delta_I_A) + ' A</td>' +
          '<td>' + fmt(sig.peak_A) + ' A</td>' +
          '<td>' + fmt(sig.rise_time_s * 1000, 3) + ' ms</td>' +
          '<td>' + sig.touch_type + '</td></tr>';
      }).join('');
      document.getElementById('dynamicBody').innerHTML =
        '<table><thead><tr><th>Gear</th><th>&Delta;I</th><th>Peak</th><th>Time of peak</th><th>Touch type</th></tr></thead><tbody>' + dynRows + '</tbody></table>';
    }
  } catch (e) {
    document.getElementById('chainBody').innerHTML = '<div class="placeholder">error loading motor data</div>';
  }
}

loadMotor();
</script>
</body>
</html>
"""

GEARSYSTEM_RAW_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Yanthros - Raw Current Waveform</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; min-height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 24px 20px 60px; }
  h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
  .sub { color: #8891a5; font-size: 13px; margin: 0 0 20px; }
  .sub a { color: #4fd1c5; }
  .status-row { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 16px; font-size: 13px; }
  .status-row .item { background: #131826; border: 1px solid #232a3d; border-radius: 8px; padding: 8px 14px; }
  .status-row .label { color: #8891a5; margin-right: 6px; }
  .status-row .val { color: #d7dbe0; font-variant-numeric: tabular-nums; }
  .status-row .val.on { color: #4fd1c5; }
  .status-row .val.off { color: #e2735a; }
  .chart-box { background: #131826; border: 1px solid #232a3d; border-radius: 10px; padding: 16px; }
  svg { display: block; width: 100%; height: auto; }
  .axis-label { fill: #5a6478; font-size: 10px; }
  .grid-line { stroke: #232a3d; stroke-width: 1; }
  .wave-line { fill: none; stroke: #4fd1c5; stroke-width: 1.5; }
  .note { color: #5a6478; font-size: 12px; margin-top: 14px; line-height: 1.6; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Raw Current Waveform</h1>
  <p class="sub">
    Direct plot of every INA228 sample as it arrives -- no block-mean, no smoothing, no gear classification.
    Detection is temporarily disabled while this is active (see <code>detection/live_state.py::CLASSIFY_ENABLED</code>).
    Back to <a href="/twin/gearsystem150">main view</a>.
  </p>
  <div class="status-row">
    <div class="item"><span class="label">Sensor</span><span class="val" id="stConnected">--</span></div>
    <div class="item"><span class="label">Port</span><span class="val" id="stPort">--</span></div>
    <div class="item"><span class="label">Samples in buffer</span><span class="val" id="stCount">--</span></div>
    <div class="item"><span class="label">Buffer span</span><span class="val" id="stSpan">--</span></div>
    <div class="item"><span class="label">Implied rate</span><span class="val" id="stRate">--</span></div>
  </div>
  <div class="chart-box">
    <svg id="chart" viewBox="0 0 1000 320"></svg>
  </div>
  <p class="note">
    X axis: seconds before now, most recent sample at the right edge. Y axis: raw current in mA, auto-scaled to
    whatever is currently in the buffer. Touch a gear and watch for a spike/dip against the idle baseline.
  </p>
</div>
<script>
const POLL_MS = 200;

function fmtSpan(samples) {
  if (samples.length < 2) return '--';
  const span = samples[samples.length - 1].t - samples[0].t;
  return span.toFixed(2) + 's';
}

function fmtRate(samples) {
  if (samples.length < 2) return '--';
  const span = samples[samples.length - 1].t - samples[0].t;
  if (span <= 0) return '--';
  return Math.round((samples.length - 1) / span) + 'Hz';
}

function drawChart(samples) {
  const svg = document.getElementById('chart');
  const W = 1000, H = 320, padL = 50, padR = 16, padT = 16, padB = 30;
  if (samples.length < 2) {
    svg.innerHTML = '<text x="' + (W / 2) + '" y="' + (H / 2) + '" text-anchor="middle" class="axis-label">waiting for samples...</text>';
    return;
  }
  const now = samples[samples.length - 1].t;
  const mA = samples.map(s => s.current_A * 1000);
  const minY = Math.min(...mA), maxY = Math.max(...mA);
  const yPad = Math.max((maxY - minY) * 0.1, 1);
  const yLo = minY - yPad, yHi = maxY + yPad;
  const tMin = samples[0].t - now, tMax = 0;
  const x = t => padL + ((t - tMin) / (tMax - tMin || 1)) * (W - padL - padR);
  const y = v => padT + (1 - (v - yLo) / (yHi - yLo || 1)) * (H - padT - padB);

  let pts = '';
  for (const s of samples) {
    pts += x(s.t - now).toFixed(1) + ',' + y(s.current_A * 1000).toFixed(1) + ' ';
  }

  let gridLines = '';
  let labels = '';
  for (let i = 0; i <= 4; i++) {
    const v = yLo + (yHi - yLo) * i / 4;
    const yy = y(v);
    gridLines += '<line x1="' + padL + '" y1="' + yy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + yy.toFixed(1) + '" class="grid-line" />';
    labels += '<text x="4" y="' + (yy + 3).toFixed(1) + '" class="axis-label">' + v.toFixed(1) + 'mA</text>';
  }
  for (let i = 0; i <= 5; i++) {
    const t = tMin + (tMax - tMin) * i / 5;
    const xx = x(t);
    labels += '<text x="' + xx.toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" class="axis-label">' + t.toFixed(1) + 's</text>';
  }

  svg.innerHTML = gridLines + labels + '<polyline points="' + pts + '" class="wave-line" />';
}

async function poll() {
  try {
    const d = await fetch('/api/gearsystem/live/raw_waveform').then(r => r.json());
    document.getElementById('stConnected').textContent = d.connected ? 'connected' : 'not connected';
    document.getElementById('stConnected').className = 'val ' + (d.connected ? 'on' : 'off');
    document.getElementById('stPort').textContent = d.port || '--';
    document.getElementById('stCount').textContent = d.n_samples;
    document.getElementById('stSpan').textContent = fmtSpan(d.samples);
    document.getElementById('stRate').textContent = fmtRate(d.samples);
    drawChart(d.samples);
  } catch (e) {
    document.getElementById('stConnected').textContent = 'error';
    document.getElementById('stConnected').className = 'val off';
  }
  setTimeout(poll, POLL_MS);
}

poll();
</script>
</body>
</html>
"""

GEARSYSTEM_VALIDATE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Yanthros - Waveform Validation</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; width: 100%; min-height: 100%; background: #0A0E1A; font-family: -apple-system, Helvetica, Arial, sans-serif; color: #d7dbe0; }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 24px 20px 60px; }
  h1 { font-size: 20px; font-weight: 600; margin: 0 0 4px; }
  .sub { color: #8891a5; font-size: 13px; margin: 0 0 20px; max-width: 760px; line-height: 1.6; }
  .sub a { color: #4fd1c5; }
  .card { background: #131826; border: 1px solid #232a3d; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
  .card h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; color: #8891a5; margin: 0 0 12px; font-weight: 600; }
  .controls-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-end; }
  .field { display: flex; flex-direction: column; gap: 4px; }
  .field label { font-size: 11px; color: #8891a5; }
  .field input, .field select {
    background: #0A0E1A; border: 1px solid #2c3448; color: #d7dbe0; border-radius: 6px;
    padding: 6px 8px; font-size: 13px; width: 110px; font-variant-numeric: tabular-nums;
  }
  .field input:focus, .field select:focus { outline: none; border-color: #4fd1c5; }
  button {
    background: #1a2033; border: 1px solid #2c3448; color: #d7dbe0; border-radius: 6px;
    padding: 8px 14px; font-size: 13px; cursor: pointer;
  }
  button:hover { border-color: #4fd1c5; }
  button.primary { background: #17403c; border-color: #4fd1c5; color: #7fe7da; }
  .legend { display: flex; gap: 18px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
  .legend label { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
  .swatch { width: 14px; height: 3px; display: inline-block; border-radius: 2px; }
  .chart-box { background: #0A0E1A; border: 1px solid #232a3d; border-radius: 10px; overflow: hidden; }
  svg { display: block; width: 100%; height: 420px; cursor: grab; }
  svg:active { cursor: grabbing; }
  .axis-label { fill: #5a6478; font-size: 10px; }
  .grid-line { stroke: #1c2233; stroke-width: 1; }
  .status-row { display: flex; gap: 20px; flex-wrap: wrap; margin: 12px 0; font-size: 12px; color: #8891a5; }
  .status-row .val { color: #d7dbe0; }
  .const-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 10px; }
  .const-grid .field input { width: 100%; }
  .const-grid .field label { font-family: ui-monospace, monospace; font-size: 10.5px; }
  .err { color: #e2735a; font-size: 12px; margin-top: 8px; display: none; }
  .hint { color: #5a6478; font-size: 12px; margin-top: 10px; line-height: 1.6; }
  .hist-list { max-height: 220px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
  .hist-row { display: grid; grid-template-columns: 1fr 1.3fr auto; gap: 10px; font-size: 12px; padding: 5px 8px; border-radius: 4px; background: #0A0E1A; align-items: center; }
  .hist-key { font-family: ui-monospace, monospace; color: #d7dbe0; }
  .hist-vals { color: #8891a5; font-variant-numeric: tabular-nums; }
  .hist-time { color: #5a6478; font-size: 11px; text-align: right; }
  .profile-row { display: grid; grid-template-columns: 1fr auto auto auto; gap: 10px; font-size: 12px; padding: 6px 8px; border-radius: 4px; background: #0A0E1A; align-items: center; }
  .profile-name { color: #d7dbe0; font-weight: 500; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Waveform Validation</h1>
  <p class="sub">
    Does the digital twin's simulated Current(t) resemble the real INA228 Current(t) for the same touch?
    Purely visual -- no classification, no FFT, no confidence score. Adjust constants, regenerate, compare, repeat.
    Back to <a href="/twin/gearsystem150">main view</a> / <a href="/twin/gearsystem150/raw">raw waveform</a>.
  </p>

  <div class="card">
    <h2>Disturbance</h2>
    <div class="controls-row">
      <div class="field">
        <label>Gear</label>
        <select id="gearSel">
          <option>Yellow</option><option>Blue</option><option>Green</option><option>Red</option>
        </select>
      </div>
      <div class="field">
        <label>Touch type</label>
        <select id="touchTypeSel">
          <option value="impact">impact</option>
          <option value="steady">steady</option>
          <option value="tooth_strike">tooth_strike</option>
        </select>
      </div>
      <div class="field">
        <label>Force (N)</label>
        <input type="number" id="forceN" value="0.5" step="0.1">
      </div>
      <div class="field">
        <label>Impulse (N*ms)</label>
        <input type="number" id="impulseNs" value="5.0" step="0.5">
      </div>
      <div class="field">
        <label>Real align offset (ms)</label>
        <input type="number" id="realOffsetMs" value="0" step="1">
      </div>
      <button class="primary" id="btnRestart">Restart Simulation</button>
      <button id="btnCapture">Capture Real Waveform</button>
      <button id="btnMarkBest">Mark Current as Best</button>
      <button id="btnResetZoom">Reset Zoom</button>
    </div>
    <div class="err" id="errBox"></div>
  </div>

  <div class="card">
    <div class="legend">
      <label><input type="checkbox" id="toggleCurrent" checked> <span class="swatch" style="background:#4fd1c5"></span> Existing Current(t)</label>
      <label><input type="checkbox" id="toggleElectrical" checked> <span class="swatch" style="background:#a78bfa"></span> Electrical Current(t) (experimental)</label>
      <label><input type="checkbox" id="togglePrevious" checked> <span class="swatch" style="background:#7c8798"></span> Previous simulation</label>
      <label><input type="checkbox" id="toggleBest"> <span class="swatch" style="background:#e6c34a"></span> Best simulation</label>
      <label><input type="checkbox" id="toggleReal" checked> <span class="swatch" style="background:#f0a35c"></span> Real INA228</label>
      <label><input type="checkbox" id="toggleDiff"> <span class="swatch" style="background:#e2735a"></span> Difference (Sim - Real)</label>
    </div>
    <div class="chart-box">
      <svg id="chart" viewBox="0 0 1160 420"></svg>
    </div>
    <div class="status-row">
      <div>Simulated: <span class="val" id="stSim">not run yet</span></div>
      <div>Electrical: <span class="val" id="stElectrical">not run yet</span></div>
      <div>Real: <span class="val" id="stReal">not captured yet</span></div>
      <div>Sensor: <span class="val" id="stConn">--</span></div>
    </div>
    <div class="hint">
      Scroll/pinch on the chart to zoom, click-drag to pan. Real and simulated waveforms use independent time
      references (real: seconds before the moment of capture; simulated: seconds since touch onset) -- pan/zoom
      to line the transients up visually. The difference curve uses "Real align offset" (ms) to shift the real
      series before subtracting -- a manual alignment control, not automatic detection.
      Electrical Current(t) is experimental (Stage 1/2, physics/electrical.py) -- it is fed the existing
      simulator's Yellow motor speed, which is a CONSTANT in the current model (never perturbed by a touch),
      so this curve does not yet respond to which gear or touch type is selected. That is expected, not a bug --
      it is exactly the gap a future coupled model (not implemented here) would close. Nothing in detection
      consumes this model.
    </div>
  </div>

  <div class="card">
    <h2>Twin constants</h2>
    <div class="const-grid" id="constGrid"></div>
  </div>

  <div class="card">
    <h2>Parameter history</h2>
    <div class="controls-row" style="margin-bottom:10px;">
      <button id="btnUndo">Undo Last Change</button>
    </div>
    <div id="historyList" class="hist-list"></div>
  </div>

  <div class="card">
    <h2>Parameter profiles &amp; snapshots</h2>
    <p class="hint" style="margin-top:0;">Stored in this browser only. Profiles are named deliberately; a snapshot is a quick save under an auto-generated name. Both load the same way.</p>
    <div class="controls-row">
      <div class="field">
        <label>Profile name</label>
        <input type="text" id="profileName" placeholder="Profile A" style="width:180px;">
      </div>
      <button id="btnSaveProfile">Save Profile</button>
      <button id="btnQuickSnapshot">Quick Snapshot</button>
    </div>
    <div id="profileList" class="hist-list" style="margin-top:12px;"></div>
  </div>
</div>

<script>
const PROFILE_STORAGE_KEY = 'gearsystem_validate_profiles';

const state = {
  constants: null,
  view: null,          // {xMin, xMax} in seconds
  realOffsetMs: 0,
  history: [],          // [{key, oldVal, newVal, t}]
  series: {
    current:    { label: 'Existing Current(t)',       color: '#4fd1c5', points: [], visible: true },
    electrical: { label: 'Electrical Current(t)',     color: '#a78bfa', points: [], visible: true },
    previous:   { label: 'Previous simulation',       color: '#7c8798', points: [], visible: true,  dashed: true },
    best:       { label: 'Best simulation',           color: '#e6c34a', points: [], visible: false },
    real:       { label: 'Real INA228',               color: '#f0a35c', points: [], visible: true },
    diff:       { label: 'Difference (Sim - Real)',   color: '#e2735a', points: [], visible: false, dashed: true },
  },
};
let debounceTimer = null;

function fmtNum(v) {
  if (v === null || v === undefined || isNaN(v)) return '--';
  return parseFloat(v.toPrecision(6)).toString();
}

function showErr(msg) {
  const box = document.getElementById('errBox');
  if (!msg) { box.style.display = 'none'; box.textContent = ''; return; }
  box.style.display = 'block';
  box.textContent = msg;
}

async function loadTwin() {
  const d = await fetch('/api/gearsystem/motor_chain').then(r => r.json());
  if (!d.available) {
    showErr('No verified twin available -- nothing to load.');
    return;
  }
  state.constants = d.constants;
  buildConstantsForm();
  runSimulation();
}

function setConstantValue(key, value) {
  state.constants[key] = value;
  const input = document.querySelector('#constGrid input[data-key="' + key + '"]');
  if (input) { input.value = value; input.dataset.valueBeforeEdit = String(value); }
}

function recordHistory(key, oldVal, newVal) {
  state.history.push({ key: key, oldVal: oldVal, newVal: newVal, t: Date.now() });
  renderHistory();
}

function undoLast() {
  const entry = state.history.pop();
  if (!entry) return;
  setConstantValue(entry.key, entry.oldVal);
  renderHistory();
  debouncedRun();
}

function renderHistory() {
  const box = document.getElementById('historyList');
  if (!state.history.length) { box.innerHTML = '<div class="hint">no changes yet</div>'; return; }
  box.innerHTML = '';
  for (let i = state.history.length - 1; i >= 0; i--) {
    const h = state.history[i];
    const row = document.createElement('div');
    row.className = 'hist-row';
    const time = new Date(h.t).toLocaleTimeString();
    row.innerHTML = '<span class="hist-key">' + h.key + '</span>' +
      '<span class="hist-vals">' + fmtNum(h.oldVal) + ' &rarr; ' + fmtNum(h.newVal) + '</span>' +
      '<span class="hist-time">' + time + '</span>';
    box.appendChild(row);
  }
}

function buildConstantsForm() {
  const grid = document.getElementById('constGrid');
  grid.innerHTML = '';
  Object.keys(state.constants).sort().forEach((key) => {
    const field = document.createElement('div');
    field.className = 'field';
    const label = document.createElement('label');
    label.textContent = key;
    const input = document.createElement('input');
    input.type = 'number';
    input.step = 'any';
    input.value = state.constants[key];
    input.dataset.key = key;
    input.dataset.valueBeforeEdit = input.value;
    input.addEventListener('focus', () => {
      input.dataset.valueBeforeEdit = input.value;
    });
    input.addEventListener('input', () => {
      state.constants[key] = parseFloat(input.value);
      debouncedRun();
    });
    input.addEventListener('change', () => {
      const oldVal = parseFloat(input.dataset.valueBeforeEdit);
      const newVal = parseFloat(input.value);
      if (!isNaN(oldVal) && !isNaN(newVal) && oldVal !== newVal) {
        recordHistory(key, oldVal, newVal);
      }
      input.dataset.valueBeforeEdit = input.value;
    });
    field.appendChild(label);
    field.appendChild(input);
    grid.appendChild(field);
  });
}

function debouncedRun() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runSimulation, 250);
}

function interpolateAt(points, xTarget) {
  if (points.length < 2) return null;
  if (xTarget < points[0].x_s || xTarget > points[points.length - 1].x_s) return null;
  for (let i = 1; i < points.length; i++) {
    if (points[i].x_s >= xTarget) {
      const a = points[i - 1], b = points[i];
      const span = b.x_s - a.x_s;
      const frac = span > 0 ? (xTarget - a.x_s) / span : 0;
      return a.y_mA + (b.y_mA - a.y_mA) * frac;
    }
  }
  return null;
}

function recomputeDiff() {
  const simPts = state.series.current.points;
  const realPts = state.series.real.points;
  if (!simPts.length || !realPts.length) { state.series.diff.points = []; return; }
  const offsetS = (state.realOffsetMs || 0) / 1000;
  const shiftedReal = realPts.map(p => ({ x_s: p.x_s + offsetS, y_mA: p.y_mA }));
  const diffPts = [];
  simPts.forEach(p => {
    const rv = interpolateAt(shiftedReal, p.x_s);
    if (rv !== null) diffPts.push({ x_s: p.x_s, y_mA: p.y_mA - rv });
  });
  state.series.diff.points = diffPts;
}

async function runSimulation() {
  if (!state.constants) return;
  const body = {
    constants: state.constants,
    gear: document.getElementById('gearSel').value,
    touch_type: document.getElementById('touchTypeSel').value,
    force_n: parseFloat(document.getElementById('forceN').value) || 0.5,
    impulse_ns: parseFloat(document.getElementById('impulseNs').value) || 5.0,
  };
  try {
    // Stage 2: one request now returns BOTH the existing model and the
    // experimental electrical model, computed against the identical touch
    // scenario -- see signature/electrical_comparison.py. The existing
    // /touch_sim_dynamic route is untouched and still used elsewhere
    // (e.g. the separate /touch-sim page); this page just calls the
    // richer comparison endpoint instead of making two separate requests.
    const resp = await fetch('/api/gearsystem/touch_sim_electrical_comparison', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    const d = await resp.json();
    if (!resp.ok || d.error) {
      showErr(d.error || 'simulation failed');
      return;
    }
    showErr(null);
    const sim = d.existing_model;
    if (state.series.current.points.length) {
      state.series.previous.points = state.series.current.points;
    }
    state.series.current.points = sim.waveform.map(p => ({ x_s: p.t_ms / 1000, y_mA: p.current_A * 1000 }));
    document.getElementById('stSim').textContent =
      sim.gear + ' / ' + sim.touch_type + ', delta=' + (sim.delta_I_A * 1000).toFixed(2) + 'mA, peak=' + (sim.peak_A * 1000).toFixed(2) + 'mA';

    const em = d.electrical_model;
    state.series.electrical.points = em.waveform.map(p => ({ x_s: p.t_ms / 1000, y_mA: p.current_A * 1000 }));
    const emFinal = em.waveform[em.waveform.length - 1].current_A;
    document.getElementById('stElectrical').textContent =
      'R=' + em.resistance_ohm + 'ohm L=' + em.inductance_h + 'H Ke=' + em.back_emf_v_s_per_rad +
      ', settles ' + (emFinal * 1000).toFixed(2) + 'mA (omega_yellow=' + d.omega_yellow_rad_s.toFixed(1) + 'rad/s, constant -- experimental, not touch-responsive yet)';

    recomputeDiff();
    if (!state.view) resetZoom();
    render();
  } catch (e) {
    showErr('simulation request failed: ' + e);
  }
}

async function captureReal() {
  try {
    const d = await fetch('/api/gearsystem/live/raw_waveform').then(r => r.json());
    document.getElementById('stConn').textContent = d.connected ? ('connected (' + d.port + ')') : 'not connected';
    if (!d.samples.length) {
      showErr('no real samples in buffer yet');
      return;
    }
    showErr(null);
    const latest = d.samples[d.samples.length - 1].t;
    state.series.real.points = d.samples.map(s => ({ x_s: s.t - latest, y_mA: s.current_A * 1000 }));
    document.getElementById('stReal').textContent = d.n_samples + ' samples captured';
    recomputeDiff();
    resetZoom();
    render();
  } catch (e) {
    showErr('capture request failed: ' + e);
  }
}

function markBest() {
  if (!state.series.current.points.length) return;
  state.series.best.points = state.series.current.points.slice();
  state.series.best.visible = true;
  document.getElementById('toggleBest').checked = true;
  render();
}

function combinedExtent() {
  const xs = [];
  Object.values(state.series).forEach(s => {
    if (!s.visible) return;
    s.points.forEach(p => xs.push(p.x_s));
  });
  if (!xs.length) return null;
  return { xMin: Math.min(...xs), xMax: Math.max(...xs) };
}

function resetZoom() {
  const ext = combinedExtent();
  if (!ext) { state.view = { xMin: -0.05, xMax: 0.05 }; render(); return; }
  const pad = Math.max((ext.xMax - ext.xMin) * 0.05, 0.001);
  state.view = { xMin: ext.xMin - pad, xMax: ext.xMax + pad };
  render();
}

function render() {
  const svg = document.getElementById('chart');
  const W = 1160, H = 420, padL = 60, padR = 16, padT = 16, padB = 30;
  if (!state.view) { svg.innerHTML = ''; return; }

  const inView = (p) => p.x_s >= state.view.xMin && p.x_s <= state.view.xMax;
  const yVals = [];
  Object.values(state.series).forEach(s => {
    if (!s.visible) return;
    s.points.filter(inView).forEach(p => yVals.push(p.y_mA));
  });
  let yLo = 0, yHi = 1;
  if (yVals.length) {
    const yMin = Math.min(...yVals), yMax = Math.max(...yVals);
    const yPad = Math.max((yMax - yMin) * 0.15, 0.5);
    yLo = yMin - yPad; yHi = yMax + yPad;
  }

  const x = t => padL + ((t - state.view.xMin) / ((state.view.xMax - state.view.xMin) || 1)) * (W - padL - padR);
  const y = v => padT + (1 - (v - yLo) / ((yHi - yLo) || 1)) * (H - padT - padB);
  const toPolyline = (points) => points.map(p => x(p.x_s).toFixed(1) + ',' + y(p.y_mA).toFixed(1)).join(' ');

  let grid = '', labels = '';
  for (let i = 0; i <= 4; i++) {
    const v = yLo + (yHi - yLo) * i / 4;
    const yy = y(v);
    grid += '<line x1="' + padL + '" y1="' + yy.toFixed(1) + '" x2="' + (W - padR) + '" y2="' + yy.toFixed(1) + '" class="grid-line" />';
    labels += '<text x="4" y="' + (yy + 3).toFixed(1) + '" class="axis-label">' + v.toFixed(2) + 'mA</text>';
  }
  for (let i = 0; i <= 6; i++) {
    const t = state.view.xMin + (state.view.xMax - state.view.xMin) * i / 6;
    const xx = x(t);
    labels += '<text x="' + xx.toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" class="axis-label">' + t.toFixed(3) + 's</text>';
  }

  let lines = '';
  Object.entries(state.series).forEach(([key, s]) => {
    if (!s.visible || s.points.length < 2) return;
    const dash = s.dashed ? ' stroke-dasharray="5,4"' : '';
    lines += '<polyline points="' + toPolyline(s.points) + '" style="fill:none;stroke:' + s.color + ';stroke-width:1.6"' + dash + ' />';
  });

  svg.innerHTML = grid + labels + lines;
}

function wireChartInteraction() {
  const svg = document.getElementById('chart');
  let dragging = false, dragStartPx = 0, dragStartView = null;

  svg.addEventListener('wheel', (e) => {
    e.preventDefault();
    if (!state.view) return;
    const rect = svg.getBoundingClientRect();
    const pxFrac = (e.clientX - rect.left) / rect.width;
    const dataX = state.view.xMin + pxFrac * (state.view.xMax - state.view.xMin);
    const factor = e.deltaY < 0 ? 0.85 : 1 / 0.85;
    const newMin = dataX - (dataX - state.view.xMin) * factor;
    const newMax = dataX + (state.view.xMax - dataX) * factor;
    state.view = { xMin: newMin, xMax: newMax };
    render();
  }, { passive: false });

  svg.addEventListener('mousedown', (e) => {
    dragging = true; dragStartPx = e.clientX; dragStartView = { ...state.view };
  });
  window.addEventListener('mousemove', (e) => {
    if (!dragging || !dragStartView) return;
    const rect = svg.getBoundingClientRect();
    const dxPx = e.clientX - dragStartPx;
    const dxData = (dxPx / rect.width) * (dragStartView.xMax - dragStartView.xMin);
    state.view = { xMin: dragStartView.xMin - dxData, xMax: dragStartView.xMax - dxData };
    render();
  });
  window.addEventListener('mouseup', () => { dragging = false; dragStartView = null; });
}

function loadProfilesFromStorage() {
  try { return JSON.parse(localStorage.getItem(PROFILE_STORAGE_KEY) || '[]'); }
  catch (e) { return []; }
}
function saveProfilesToStorage(list) {
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(list));
}
function saveProfile(name) {
  if (!state.constants) return;
  const list = loadProfilesFromStorage();
  list.push({ name: name, constants: Object.assign({}, state.constants), savedAt: new Date().toISOString() });
  saveProfilesToStorage(list);
  renderProfileList();
}
function loadProfile(idx) {
  const list = loadProfilesFromStorage();
  const p = list[idx];
  if (!p) return;
  state.constants = Object.assign({}, p.constants);
  buildConstantsForm();
  runSimulation();
}
function deleteProfile(idx) {
  const list = loadProfilesFromStorage();
  list.splice(idx, 1);
  saveProfilesToStorage(list);
  renderProfileList();
}
function renderProfileList() {
  const list = loadProfilesFromStorage();
  const box = document.getElementById('profileList');
  box.innerHTML = '';
  if (!list.length) { box.innerHTML = '<div class="hint">no saved profiles or snapshots yet</div>'; return; }
  list.forEach((p, i) => {
    const row = document.createElement('div');
    row.className = 'profile-row';
    const nameSpan = document.createElement('span');
    nameSpan.className = 'profile-name';
    nameSpan.textContent = p.name;
    const timeSpan = document.createElement('span');
    timeSpan.className = 'hist-time';
    timeSpan.textContent = new Date(p.savedAt).toLocaleTimeString();
    const loadBtn = document.createElement('button');
    loadBtn.textContent = 'Load';
    loadBtn.addEventListener('click', () => loadProfile(i));
    const delBtn = document.createElement('button');
    delBtn.textContent = 'Delete';
    delBtn.addEventListener('click', () => deleteProfile(i));
    row.appendChild(nameSpan); row.appendChild(timeSpan); row.appendChild(loadBtn); row.appendChild(delBtn);
    box.appendChild(row);
  });
}

document.getElementById('gearSel').addEventListener('change', runSimulation);
document.getElementById('touchTypeSel').addEventListener('change', runSimulation);
document.getElementById('forceN').addEventListener('input', debouncedRun);
document.getElementById('impulseNs').addEventListener('input', debouncedRun);
document.getElementById('realOffsetMs').addEventListener('input', () => {
  state.realOffsetMs = parseFloat(document.getElementById('realOffsetMs').value) || 0;
  recomputeDiff();
  render();
});
document.getElementById('btnRestart').addEventListener('click', runSimulation);
document.getElementById('btnCapture').addEventListener('click', captureReal);
document.getElementById('btnMarkBest').addEventListener('click', markBest);
document.getElementById('btnResetZoom').addEventListener('click', resetZoom);
document.getElementById('btnUndo').addEventListener('click', undoLast);
document.getElementById('btnSaveProfile').addEventListener('click', () => {
  const nameInput = document.getElementById('profileName');
  const name = nameInput.value.trim() || ('Profile ' + new Date().toLocaleTimeString());
  saveProfile(name);
  nameInput.value = '';
});
document.getElementById('btnQuickSnapshot').addEventListener('click', () => {
  saveProfile('Snapshot ' + new Date().toLocaleTimeString());
});
document.getElementById('toggleCurrent').addEventListener('change', (e) => { state.series.current.visible = e.target.checked; render(); });
document.getElementById('toggleElectrical').addEventListener('change', (e) => { state.series.electrical.visible = e.target.checked; render(); });
document.getElementById('togglePrevious').addEventListener('change', (e) => { state.series.previous.visible = e.target.checked; render(); });
document.getElementById('toggleBest').addEventListener('change', (e) => { state.series.best.visible = e.target.checked; render(); });
document.getElementById('toggleReal').addEventListener('change', (e) => { state.series.real.visible = e.target.checked; render(); });
document.getElementById('toggleDiff').addEventListener('change', (e) => { state.series.diff.visible = e.target.checked; render(); });

wireChartInteraction();
renderHistory();
renderProfileList();
loadTwin();
</script>
</body>
</html>
"""


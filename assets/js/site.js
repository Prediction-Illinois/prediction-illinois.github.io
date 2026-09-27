// Prediction@Illinois — site.js
(function(){
  const $ = s => document.querySelector(s);

  // theme toggle: dark by default, preference kept per browser
  const tbtn = $("#theme");
  if (tbtn) tbtn.addEventListener("click", () => {
    const r = document.documentElement, next = r.dataset.theme === "light" ? "dark" : "light";
    r.dataset.theme = next; try { localStorage.setItem("pi-theme", next); } catch (_) {}
  });

  // ---- live markets (Polymarket Gamma API, CORS-open) ----
  // Order matters: specific categories first, Politics last as the catch-all (a Fed event can carry a "Trump" tag).
  const TAGMAP = [
    [/election/i, "Elections"],
    [/sport|esport|\bgames?\b|nfl|nba|mlb|nhl|soccer|tennis|cfb|ufc|\bf1\b|golf|epl|ucl|football|baseball|basketball|hockey/i, "Sports"],
    [/crypto|bitcoin|ethereum|solana|\bbtc\b|\beth\b/i, "Crypto"],
    [/econom|\bfed\b|fomc|inflation|finance|business|stock|earnings|rates|\boil\b|commodit|treasur/i, "Economics"],
    [/tech|\bai\b|science|space|openai|apple|google|nvidia|tesla/i, "Tech"],
    [/weather|climate|temperature|hurricane|snow/i, "Weather"],
    [/politic|geopolit|congress|senate|white house|trump|iran|israel|ukraine|world/i, "Politics"]
  ];
  const mapTag = tags => { const L = (tags || []).map(t => t.label || ""); for (const [re, n] of TAGMAP) if (L.some(l => re.test(l))) return n; return L[0] || "Markets"; };
  const fmtVol = v => v >= 1e6 ? "$" + (v / 1e6).toFixed(1) + "M" : v >= 1e3 ? "$" + Math.round(v / 1e3) + "K" : "$" + Math.round(v);
  const esc = x => String(x).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // Mutually-exclusive events (negRisk: nominee, champion, Fed decision) → leading sub-market.
  // Everything else (a game, a price ladder) → most-traded sub-market, i.e. the main line, not a prop.
  // A sub-market whose question is the event title is the main line (e.g. "Army vs. Temple") — prefer it outright.
  function lead(e) {
    const title = String(e.title || "").trim().toLowerCase();
    // If the event's main line (question == title) exists but is closed, the game is over — skip the event
    // rather than surface a leftover prop market.
    const mainAny = (e.markets || []).find(m => String(m.question || "").trim().toLowerCase() === title);
    if (mainAny && (mainAny.closed || !mainAny.active)) return null;
    const ms = (e.markets || []).filter(m => m.active && !m.closed); let best = null; const byProb = !!e.negRisk;
    for (const m of ms) {
      let o, p; try { o = JSON.parse(m.outcomes); p = JSON.parse(m.outcomePrices).map(Number); } catch (_) { continue; }
      if (!o || p.length < 2) continue;
      const binary = o[0] === "Yes" && o[1] === "No", i = binary ? 0 : p.indexOf(Math.max(...p));
      const label = binary ? (ms.length > 1 ? (m.groupItemTitle || "Yes") : "Yes") : o[i];
      const main = !byProb && String(m.question || "").trim().toLowerCase() === title;
      const key = main ? Infinity : byProb ? p[i] : (+m.volume24hr || 0);
      if (!best || key > best.key) best = { prob: p[i], label, key };
    }
    return best;
  }
  const row = x => `<div class="row" data-side="${x.prob >= .5 ? "yes" : "no"}"><div class="q">${esc(x.title)}<span>${esc(x.tag)} · ${esc(x.label)} · ${fmtVol(x.vol)} 24h</span></div><div class="pct num">${Math.round(x.prob * 100)}%</div><div class="track"><i style="transform:scaleX(${x.prob.toFixed(3)})"></i></div></div>`;
  const tkItem = x => `<span class="tk" data-side="${x.prob >= .5 ? "yes" : "no"}"><span class="cat">${esc(x.tag)}</span>${esc(x.title)}<span class="num">${Math.round(x.prob * 100)}%</span></span>`;

  async function loadMarkets() {
    const board = $("#board"); if (!board) return;
    const hero = $("#hero"), rowsEl = $("#board-rows"), ticker = $("#ticker"), tk = $("#tk");
    const want = (board.dataset.tags || "").split(",").map(s => s.trim()).filter(Boolean);
    const ids = (board.dataset.tagIds || "").split(",").map(s => s.trim()).filter(Boolean);
    const limit = +board.dataset.rows || 6, perTag = (want.length || ids.length) ? 99 : 2;
    const base = "https://gamma-api.polymarket.com/events?closed=false&active=true&order=volume24hr&ascending=false";
    try {
      let events;
      if (ids.length) {
        // market page: one request per Polymarket tag id, merged and de-duplicated by event id
        const lists = await Promise.all(ids.map(id => fetch(base + "&limit=25&tag_id=" + id).then(r => r.ok ? r.json() : [])));
        const seen = new Set(); events = [];
        for (const e of lists.flat()) if (e && !seen.has(e.id)) { seen.add(e.id); events.push(e); }
        events.sort((a, b) => (+b.volume24hr || 0) - (+a.volume24hr || 0));
      } else {
        const r = await fetch(base + "&limit=40"); if (!r.ok) throw 0; events = await r.json();
      }
      const all = [];
      for (const e of events) {
        const b = lead(e); if (!b || b.prob < 0.03 || b.prob > 0.97) continue;
        const tag = mapTag(e.tags); if (want.length && !ids.length && !want.includes(tag)) continue;
        all.push({ title: e.title, tag, prob: b.prob, label: b.label, vol: +e.volume24hr || 0 });
      }
      if (all.length < (ids.length ? 1 : 4)) throw 0;
      const per = {}, top = [], rest = [];
      for (const x of all) { if (top.length < limit && (per[x.tag] || 0) < perTag) { per[x.tag] = (per[x.tag] || 0) + 1; top.push(x); } else rest.push(x); }
      rowsEl.innerHTML = top.map(row).join(""); board.hidden = false;
      const items = rest.slice(0, 14);
      if (ticker && tk && items.length >= 6) { tk.innerHTML = items.map(tkItem).join(""); tk.innerHTML += tk.innerHTML; ticker.hidden = false; }
      const empty = $("#board-empty"); if (empty) empty.hidden = true;
    } catch (_) {
      if (hero) hero.classList.add("solo");
      const empty = $("#board-empty"); if (empty) empty.hidden = false;
    }
  }
  loadMarkets();

  // ---- research: abstract toggles ----
  document.querySelectorAll("[data-abs]").forEach(b => b.addEventListener("click", () => {
    const box = b.closest(".work").querySelector(".abs"), open = box.hidden;
    box.hidden = !open; b.setAttribute("aria-expanded", String(open));
  }));

  // ---- apply page ----
  function flash(btn, word){ const old = btn.textContent; btn.textContent = word; setTimeout(() => { btn.textContent = old; }, 1600); }
  const mc = $("#mail-copy");
  if (mc) mc.addEventListener("click", async e => {
    const btn = e.currentTarget, text = ($("#mail") || {}).textContent || "";
    try { await navigator.clipboard.writeText(text); flash(btn, "Copied"); } catch (_) { flash(btn, "Select it"); }
  });

  const form = $("#apply"); if (!form) return;
  // ?market=<key> from a market page pre-checks that market
  try {
    const k = new URLSearchParams(location.search).get("market");
    if (k) form.querySelectorAll('input[name="markets"]').forEach(cb => { if (cb.dataset.key === k) cb.checked = true; });
  } catch (_) {}
  const err = $("#form-err"), btn = $("#apply-submit"), done = $("#apply-done"), ds = form.dataset;
  const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  form.addEventListener("submit", async e => {
    e.preventDefault();
    const v = n => (form.elements[n].value || "").trim();
    const markets = [...form.querySelectorAll('input[name="markets"]:checked')].map(cb => cb.value);
    const missing = [];
    if (!v("name")) missing.push("your name");
    if (!EMAIL.test(v("email"))) missing.push("a valid email");
    if (!v("year")) missing.push("your year");
    if (!v("major")) missing.push("your major");
    if (!markets.length) missing.push("at least one market");
    if (!v("question")) missing.push("your question");
    if (missing.length) { err.textContent = "Add " + missing.join(", ") + "."; err.hidden = false; return; }
    err.hidden = true; btn.disabled = true; btn.textContent = "Submitting…";
    const body = new URLSearchParams();
    body.append(ds.fName, v("name")); body.append(ds.fEmail, v("email")); body.append(ds.fYear, v("year"));
    body.append(ds.fMajor, v("major")); markets.forEach(m => body.append(ds.fMarkets, m));
    body.append(ds.fQuestion, v("question")); if (v("link")) body.append(ds.fLink, v("link"));
    try {
      await fetch(ds.post, { method: "POST", mode: "no-cors", body });   // Google Forms accepts cross-origin posts; the response is opaque
      form.hidden = true; done.hidden = false; done.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (_) {
      btn.disabled = false; btn.textContent = "Submit application";
      err.textContent = "Couldn't reach the form. Check your connection and try again, or email us."; err.hidden = false;
    }
  });
})();

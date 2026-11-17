# /// script
# dependencies = ["openpyxl"]
# ///
"""Build link_review/index.html from impl_review.xlsx (sheet `review`).

Usage:  uv run link_review/build_site.py [path/to/impl_review.xlsx]
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
URL_RE = re.compile(r"https?://\S+")


def clean_url(s):
    m = URL_RE.search(s or "")
    return m.group(0).rstrip(".,;)]>\"'") if m else ""


def read_papers(xlsx):
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb["review"]
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(rows)]
    col = {name: header.index(name) for name in ("record_id", "title", "evidence", "best_link", "other_links")}
    papers, seen = [], set()
    for r in rows:
        if r is None or all(v is None or str(v).strip() == "" for v in r):
            continue
        get = lambda k: "" if r[col[k]] is None else str(r[col[k]]).strip()
        rid = get("record_id")
        if not rid:
            sys.exit(f"ERROR: a non-empty row has no record_id: {r!r}")
        if rid in seen:
            sys.exit(f"ERROR: duplicate record_id {rid} — decisions are keyed by record_id")
        seen.add(rid)
        best = clean_url(get("best_link"))
        others = []
        for line in get("other_links").splitlines():
            url = clean_url(line)
            if not url or url == best or any(o["url"] == url for o in others):
                continue
            m = re.search(r"\[([^\]]*)\]\s*$", line)
            others.append({"url": url, "label": m.group(1) if m else ""})
        if not best and others:
            best = others.pop(0)["url"]
        papers.append({"id": rid, "title": get("title"), "ev": get("evidence").lower(),
                       "best": best, "others": others})
    wb.close()
    return papers


def main():
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "impl_review.xlsx"
    papers = read_papers(xlsx)
    canon = json.dumps(papers, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    data_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]
    payload = json.dumps({"hash": data_hash, "papers": papers}, ensure_ascii=False, separators=(",", ":"))
    # Make the JSON inert inside <script>: no "</script>", "<!--" etc. can survive.
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    html = TEMPLATE.replace("__DATA__", payload)
    out = HERE / "index.html"
    out.write_text(html, encoding="utf-8")
    no_link = [p["id"] for p in papers if not p["best"]]
    print(f"Wrote {out} — {len(papers)} papers, data hash {data_hash}")
    print(f"First: {papers[0]['id']}  Last: {papers[-1]['id']}")
    if no_link:
        print(f"WARNING: {len(no_link)} papers have no link: {', '.join(no_link)}")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Link Review</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--mute:#5d6470;--line:#d9dde3;--blue:#1f5fd1;
--g:#1e8e3e;--o:#e07800;--r:#c62828;--warnbg:#fff4d6;--errbg:#fde2e2}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--card:#1c1f24;--ink:#eceef1;--mute:#9aa2ad;--line:#333841;
--blue:#6ea0ff;--warnbg:#3a3214;--errbg:#3d1d1d}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body{overflow-x:hidden}
.wrap{max-width:680px;margin:0 auto;padding:0 16px 40px}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px}
header .in{max-width:680px;margin:0 auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
#progress{font-weight:700;font-size:17px;flex:1;min-width:0}
.cnt{display:inline-block;font-weight:700;padding:0 6px}
.cg{color:var(--g)}.co{color:var(--o)}.cr{color:var(--r)}
button,.btn{font:inherit;cursor:pointer;border-radius:12px;border:2px solid var(--line);background:var(--card);color:var(--ink);
min-height:48px;padding:8px 14px;touch-action:manipulation;-webkit-tap-highlight-color:transparent;text-decoration:none;display:inline-flex;align-items:center;justify-content:center}
button:active,.btn:active{transform:scale(.98)}
#dl{font-weight:700;border-color:var(--blue);color:var(--blue)}
.banner{margin:12px 0;padding:12px 14px;border-radius:10px;font-weight:600;display:none}
.banner.show{display:block}
.warn{background:var(--warnbg)}.err{background:var(--errbg)}
details{margin:12px 0;background:var(--card);border:1px solid var(--line);border-radius:12px}
summary{padding:12px 14px;font-weight:700;cursor:pointer;min-height:48px;display:flex;align-items:center}
details ul{margin:0;padding:0 14px 12px 32px}details p{margin:0;padding:0 14px 12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}
.meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;color:var(--mute);font-size:14px}
.rid{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;color:var(--ink);font-size:15px}
.ev{padding:2px 8px;border-radius:999px;font-weight:700;font-size:13px;text-transform:uppercase;border:1px solid var(--line)}
.ev-strong{color:var(--g)}.ev-medium{color:var(--o)}.ev-weak{color:var(--r)}
h1{font-size:19px;margin:8px 0 0;overflow-wrap:anywhere}
.rated{margin-top:10px;font-weight:700;padding:8px 10px;border-radius:8px;border:2px solid currentColor}
.links{display:flex;flex-direction:column;gap:10px}
.lk{width:100%;flex-direction:column;align-items:flex-start;text-align:left;overflow-wrap:anywhere}
.lk .u{font-size:13px;color:var(--mute);word-break:break-all}
.lk.best{min-height:72px;border-color:var(--blue);font-weight:700;font-size:18px;color:var(--blue)}
.lk.other{font-size:15px}
.lk.last{box-shadow:0 0 0 3px var(--blue)}
.lk .tag{font-size:12px;font-weight:700;color:var(--blue)}
textarea{width:100%;font:inherit;padding:12px;border-radius:12px;border:2px solid var(--line);background:var(--card);color:var(--ink);resize:vertical;min-height:52px}
.rate{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:16px 0}
.rate button{min-height:96px;font-size:20px;font-weight:800;color:#fff;border:none;flex-direction:column;gap:2px}
.rate button small{font-size:12px;font-weight:600;opacity:.85}
#bG{background:var(--g)}#bO{background:var(--o)}#bR{background:var(--r)}
.rate button.cur{outline:5px solid var(--ink);outline-offset:3px}
.rate button:disabled{opacity:.35}
.row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.row button{font-size:15px}
.tools{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}
#toast{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);max-width:calc(100% - 32px);background:var(--ink);color:var(--bg);
padding:12px 16px;border-radius:10px;font-weight:600;opacity:0;transition:opacity .2s;pointer-events:none;z-index:9}
#toast.show{opacity:1}
.done{text-align:center;font-size:20px;font-weight:700;padding:24px 0}
.hint{color:var(--mute);font-size:13px;margin-top:14px;text-align:center}
@media (max-width:420px){.rate{gap:10px}.rate button{font-size:18px;min-height:88px}}
</style>
</head>
<body>
<header><div class="in">
  <div id="progress">…</div>
  <button id="dl" type="button">Download decisions</button>
</div></header>
<div class="wrap">
  <div id="storeErr" class="banner err">Browser storage is unavailable or failing. Your ratings are kept only while this tab stays open. Use “Download decisions” often.</div>
  <div id="ckpt" class="banner warn"></div>
  <div id="oldData" class="banner warn"></div>

  <details>
    <summary>Rating criteria</summary>
    <ul>
      <li><b>A1 Accessible:</b> opens without login; not empty or a placeholder</li>
      <li><b>A2 Author-created:</b> owned by an author or their org, or stated as official</li>
      <li><b>A3 Relevant:</b> README names the paper (title, system name, arXiv id, DOI), or the paper calls it its own code</li>
      <li><b>A4 Adds value:</b> contains source code for the mechanism, not only docs, data or results</li>
    </ul>
    <p><b class="cg">GREEN</b> = all four clearly met. <b class="co">ORANGE</b> = met, but doubtful on completeness or provenance. <b class="cr">RED</b> = any one fails.</p>
  </details>

  <div id="paper" class="card"></div>
  <div id="links" class="links"></div>

  <div style="margin-top:14px"><textarea id="note" rows="1" placeholder="Optional note"></textarea></div>

  <div class="rate">
    <button id="bG" type="button" data-d="GREEN">GREEN<small>key 1</small></button>
    <button id="bO" type="button" data-d="ORANGE">ORANGE<small>key 2</small></button>
    <button id="bR" type="button" data-d="RED">RED<small>key 3</small></button>
  </div>
  <div class="row">
    <button id="back" type="button">◀ Back</button>
    <button id="jump" type="button">Jump to #</button>
    <button id="again" type="button">Open link again</button>
  </div>
  <div class="tools">
    <button id="imp" type="button">Import decisions</button>
    <button id="dl2" type="button">Download decisions</button>
  </div>
  <input id="file" type="file" accept=".csv,text/csv" hidden>
  <div class="hint">Keys: 1 GREEN · 2 ORANGE · 3 RED · B back · O open link again</div>
</div>
<div id="toast"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
"use strict";
const DATA = JSON.parse(document.getElementById("data").textContent);
const P = DATA.papers, N = P.length;
const PREFIX = "impl_review_v1_", KEY = PREFIX + DATA.hash;
const IDX = new Map(P.map((p, i) => [p.id, i]));
const DECS = ["GREEN", "ORANGE", "RED"];
const CHECKPOINT_EVERY = 50;
const $ = id => document.getElementById(id);

let state = { decisions: {}, lastOpened: {}, sinceCheckpoint: 0 };
let cur = 0, lockUntil = 0, storageBroken = false, shownId = null;

// ---------- storage (every call guarded; falls back to memory) ----------
function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
function lsKeys() { try { return Object.keys(localStorage); } catch (e) { return []; } }
function readStored(k) {
  try { const s = JSON.parse(lsGet(k) || "null"); return s && typeof s === "object" ? s : null; } catch (e) { return null; }
}
const t = d => { const x = Date.parse(d && d.decided_at); return isNaN(x) ? -Infinity : x; };
// Merge src decisions into dst; a src entry wins only if strictly newer. Returns number changed.
function mergeDecisions(dst, src) {
  let n = 0;
  for (const id in src || {}) {
    const d = src[id];
    if (!IDX.has(id) || !d || !DECS.includes(d.decision)) continue;
    if (!dst[id] || t(d) > t(dst[id])) { dst[id] = { ...d, position: IDX.get(id) + 1 }; n++; }
  }
  return n;
}
function save() {
  // Pick up anything another tab saved first, so two open tabs never clobber each other.
  const other = readStored(KEY);
  if (other) {
    mergeDecisions(state.decisions, other.decisions);
    for (const id in other.lastOpened || {}) if (!(id in state.lastOpened)) state.lastOpened[id] = other.lastOpened[id];
  }
  const s = JSON.stringify(state);
  const ok = lsSet(KEY, s) && lsGet(KEY) === s;
  setStorageBroken(!ok);
  return ok;
}
function setStorageBroken(b) { storageBroken = b; $("storeErr").classList.toggle("show", b); }
function load() {
  const s = readStored(KEY);
  if (s) {
    mergeDecisions(state.decisions, s.decisions);
    if (s.lastOpened && typeof s.lastOpened === "object") state.lastOpened = s.lastOpened;
    state.sinceCheckpoint = +s.sinceCheckpoint || 0;
  }
  const probe = PREFIX + "probe";
  setStorageBroken(!(lsSet(probe, "1") && lsGet(probe) === "1"));
  try { localStorage.removeItem(probe); } catch (e) {}
  try { navigator.storage && navigator.storage.persist && navigator.storage.persist(); } catch (e) {}
  // Progress saved by an older build of this page (different data hash) — offer to recover it.
  if (!Object.keys(state.decisions).length) {
    const old = {};
    for (const k of lsKeys()) if (k.startsWith(PREFIX) && k !== KEY && k !== probe) {
      const o = readStored(k); if (o) mergeDecisions(old, o.decisions);
    }
    const n = Object.keys(old).length;
    if (n) {
      const b = $("oldData");
      b.innerHTML = "";
      b.append(`Found ${n} ratings saved by an older build of this page. `);
      const btn = document.createElement("button");
      btn.textContent = "Recover them";
      btn.onclick = () => { mergeDecisions(state.decisions, old); save(); b.classList.remove("show"); go(firstUnrated()); toast(`Recovered ${n} ratings`); };
      b.append(btn); b.classList.add("show");
    }
  }
}
window.addEventListener("storage", e => {
  if (e.key !== KEY) return;
  const o = readStored(KEY);
  if (o && mergeDecisions(state.decisions, o.decisions)) render();
});

// ---------- navigation ----------
const rated = i => !!state.decisions[P[i].id];
function firstUnrated() { for (let i = 0; i < N; i++) if (!rated(i)) return i; return N; }
function nextUnrated(from) {
  for (let i = from + 1; i < N; i++) if (!rated(i)) return i;
  for (let i = 0; i < from && i < N; i++) if (!rated(i)) return i;
  return N;
}
function go(i) { cur = Math.max(0, Math.min(N, i)); render(); window.scrollTo(0, 0); }

function openUrl(url) {
  if (!url) return;
  const w = window.open(url, "_blank");
  if (w) { try { w.opener = null; } catch (e) {} }
  else toast("Popup blocked — tap the link button to open it", 4000);
}
function linkFor(i) { const p = P[i]; return state.lastOpened[p.id] || p.best; }

// ---------- rating ----------
function rate(dec) {
  if (cur >= N || Date.now() < lockUntil) return;   // lock stops an accidental double tap rating two papers
  lockUntil = Date.now() + 700;
  const p = P[cur];
  state.decisions[p.id] = {
    decision: dec, link_judged: linkFor(cur), note: $("note").value.trim(),
    decided_at: new Date().toISOString(), position: cur + 1,
  };
  state.sinceCheckpoint++;
  const nxt = nextUnrated(cur);
  if (nxt < N) state.lastOpened[P[nxt].id] = P[nxt].best;
  const ok = save();
  if (nxt < N) openUrl(P[nxt].best);   // same click => not popup-blocked
  go(nxt);
  toast(`${ok ? "Saved" : "Saved in memory only"}: #${p.id} → ${dec}`);
  if (state.sinceCheckpoint >= CHECKPOINT_EVERY) {
    const name = download();
    const b = $("ckpt");
    b.textContent = `Checkpoint: downloaded ${name} (${Object.keys(state.decisions).length} decisions) at ${new Date().toLocaleTimeString()}. Keep it safe.`;
    b.classList.add("show");
  }
}

// ---------- CSV ----------
const q = v => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
function buildCSV() {
  const cols = ["record_id", "decision", "link_judged", "note", "decided_at", "position"];
  const lines = [cols.map(q).join(",")];
  const ids = Object.keys(state.decisions).sort((a, b) => IDX.get(a) - IDX.get(b));
  for (const id of ids) {
    const d = state.decisions[id];
    lines.push([id, d.decision, d.link_judged, d.note, d.decided_at, IDX.get(id) + 1].map(q).join(","));
  }
  return "\ufeff" + lines.join("\r\n") + "\r\n";
}
function download() {
  const n = Object.keys(state.decisions).length;
  const d = new Date(), z = x => String(x).padStart(2, "0");
  const stamp = `${d.getFullYear()}${z(d.getMonth() + 1)}${z(d.getDate())}-${z(d.getHours())}${z(d.getMinutes())}`;
  const name = `impl_decisions_${n}_${stamp}.csv`;
  const url = URL.createObjectURL(new Blob([buildCSV()], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url; a.download = name; a.style.display = "none";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
  state.sinceCheckpoint = 0; save();
  return name;
}
function parseCSV(text) {
  text = text.replace(/^\ufeff/, "");
  const rows = []; let row = [], f = "", inq = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inq) {
      if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else inq = false; }
      else f += c;
    } else if (c === '"') inq = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n") { row.push(f); rows.push(row); row = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f !== "" || row.length) { row.push(f); rows.push(row); }
  return rows;
}
function importCSV(text) {
  const rows = parseCSV(text);
  if (!rows.length) throw new Error("empty file");
  const h = rows[0].map(s => s.trim());
  const ix = k => h.indexOf(k);
  for (const k of ["record_id", "decision", "decided_at"]) if (ix(k) < 0) throw new Error("missing column " + k);
  const src = {}; let unknown = 0, bad = 0;
  for (const r of rows.slice(1)) {
    if (r.length === 1 && r[0] === "") continue;
    const id = (r[ix("record_id")] || "").trim(), dec = (r[ix("decision")] || "").trim().toUpperCase();
    if (!IDX.has(id)) { unknown++; continue; }
    if (!DECS.includes(dec) || isNaN(Date.parse(r[ix("decided_at")]))) { bad++; continue; }
    const d = { decision: dec, decided_at: r[ix("decided_at")].trim(),
      link_judged: ix("link_judged") >= 0 ? r[ix("link_judged")] : P[IDX.get(id)].best,
      note: ix("note") >= 0 ? r[ix("note")] : "" };
    if (!src[id] || t(d) > t(src[id])) src[id] = d;
  }
  const changed = mergeDecisions(state.decisions, src);
  const ok = save();
  go(firstUnrated());
  return `Imported: ${changed} new/updated, ${Object.keys(src).length - changed} already up to date` +
    (unknown ? `, ${unknown} unknown record_ids skipped` : "") + (bad ? `, ${bad} bad rows skipped` : "") +
    (ok ? "" : " (storage failing — kept in memory)");
}

// ---------- render ----------
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function render() {
  const vals = Object.values(state.decisions);
  const c = k => vals.filter(d => d.decision === k).length;
  const pr = $("progress"); pr.innerHTML = "";
  pr.append(`${vals.length} / ${N} rated `);
  for (const [k, cl] of [["G", "cg"], ["O", "co"], ["R", "cr"]])
    pr.append(el("span", "cnt " + cl, `${k} ${c({ G: "GREEN", O: "ORANGE", R: "RED" }[k])}`));

  const paper = $("paper"), links = $("links");
  paper.innerHTML = ""; links.innerHTML = "";
  const done = cur >= N;
  for (const b of document.querySelectorAll(".rate button")) { b.disabled = done; b.classList.remove("cur"); }
  $("again").disabled = done;
  if (done) {
    const left = N - vals.length;
    paper.append(el("div", "done", left ? `End of list — ${left} still unrated (use Jump to #)` : `All ${N} papers rated 🎉`));
    paper.append(el("div", "hint", "Press Download decisions to save the CSV."));
    $("note").value = ""; shownId = null;
    return;
  }
  const p = P[cur], d = state.decisions[p.id];
  const meta = el("div", "meta");
  meta.append(el("span", "rid", p.id), el("span", "", `#${cur + 1} of ${N}`), el("span", "ev ev-" + p.ev, p.ev || "?"));
  paper.append(meta, el("h1", "", p.title));
  if (d) {
    const r = el("div", "rated " + { GREEN: "cg", ORANGE: "co", RED: "cr" }[d.decision],
      `Already rated ${d.decision} — press a colour to change it`);
    paper.append(r);
    $({ GREEN: "bG", ORANGE: "bO", RED: "bR" }[d.decision]).classList.add("cur");
  }
  const last = linkFor(cur);
  const mk = (url, cls, label) => {
    const a = el("a", "btn lk " + cls + (url === last ? " last" : ""));
    a.href = url; a.target = "_blank"; a.rel = "noopener";
    a.append(el("span", "", label));
    a.append(el("span", "u", url));
    if (url === last) a.append(el("span", "tag", "▲ judged link"));
    a.addEventListener("click", () => { state.lastOpened[p.id] = url; save(); setTimeout(render, 0); });
    return a;
  };
  links.append(mk(p.best, "best", "Open best link ↗"));
  for (const o of p.others) links.append(mk(o.url, "other", `Other link${o.label ? " [" + o.label + "]" : ""} ↗`));
  if (shownId !== p.id) { $("note").value = d ? d.note || "" : ""; shownId = p.id; }  // don't wipe a note being typed
}

let toastTimer;
function toast(msg, ms = 1800) {
  const e = $("toast"); e.textContent = msg; e.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => e.classList.remove("show"), ms);
}

// ---------- wiring ----------
for (const b of document.querySelectorAll(".rate button")) b.addEventListener("click", () => rate(b.dataset.d));
$("back").onclick = () => go(cur - 1);
$("again").onclick = () => { if (cur < N) openUrl(linkFor(cur)); };
$("jump").onclick = () => {
  const s = prompt(`Go to # (1–${N})`, String(Math.min(cur + 1, N)));
  if (s == null) return;
  const n = parseInt(s, 10);
  if (n >= 1 && n <= N) go(n - 1); else toast("Not a valid number");
};
$("dl").onclick = $("dl2").onclick = () => toast("Downloaded " + download(), 3000);
$("imp").onclick = () => $("file").click();
$("file").onchange = async e => {
  const f = e.target.files[0]; e.target.value = "";
  if (!f) return;
  try { toast(importCSV(await f.text()), 5000); } catch (err) { toast("Import failed: " + err.message, 5000); }
};
document.addEventListener("keydown", e => {
  if (e.ctrlKey || e.metaKey || e.altKey || e.repeat) return;
  const tg = e.target.tagName;
  if (tg === "TEXTAREA" || tg === "INPUT") { if (e.key === "Escape") e.target.blur(); return; }
  const k = e.key.toLowerCase();
  if (k === "1") rate("GREEN"); else if (k === "2") rate("ORANGE"); else if (k === "3") rate("RED");
  else if (k === "b") go(cur - 1);
  else if (k === "o" && cur < N) openUrl(linkFor(cur));
  else return;
  e.preventDefault();
});

load();
go(firstUnrated());
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

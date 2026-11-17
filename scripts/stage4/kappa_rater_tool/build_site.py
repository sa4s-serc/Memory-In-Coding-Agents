# ///
# dependencies = []
# ///
"""Build kappa_review/index.html: the rater page for the 30-paper agreement check.

Reads sample_30.csv (what to show) and ../prompt.md (the criteria, shown unchanged).
It never reads ai_labels_30.csv, so the page carries no AI labels.

Usage:  python3 kappa_review/build_site.py
"""
import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def read_papers():
    papers, seen = [], set()
    for r in csv.DictReader(open(HERE / "sample_30.csv", encoding="utf-8-sig")):
        rid = r["record_id"].strip()
        if rid in seen:
            sys.exit(f"ERROR: duplicate record_id {rid}")
        seen.add(rid)
        if not (HERE / r["local_pdf"]).exists():
            sys.exit(f"ERROR: {r['local_pdf']} is missing; run make_sample.py")
        links = [{"label": "Open paper (PDF)", "url": r["local_pdf"]}, {"label": "Online", "url": r["online_link"]}]
        if r["arxiv_id"] and r["doi"]:
            links.append({"label": "DOI", "url": "https://doi.org/" + r["doi"]})
        papers.append({"id": rid, "title": r["title"], "links": links})
    return papers


def criteria_html():
    """Steps 0-4 of prompt.md, word for word. Only **bold** is turned into <b>."""
    lines = (ROOT / "prompt.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## STEP 0"))
    end = next(i for i, l in enumerate(lines) if l.startswith("## OUTPUT"))
    text = "\n".join(lines[start:end]).strip("\n")
    esc = html.escape(text)
    esc = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc, flags=re.S)
    esc = re.sub(r"^## (.*)$", r"<b class=\"stp\">\1</b>", esc, flags=re.M)
    return esc


def main():
    papers = read_papers()
    canon = json.dumps(papers, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    data_hash = hashlib.sha256(canon.encode("utf-8")).hexdigest()[:12]
    payload = json.dumps({"hash": data_hash, "papers": papers}, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    payload = payload.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    page = TEMPLATE.replace("__CRITERIA__", criteria_html()).replace("__DATA__", payload)
    out = HERE / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"Wrote {out} - {len(papers)} papers, data hash {data_hash}")
    print(f"First: {papers[0]['id']}  Last: {papers[-1]['id']}")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Paper classification (rater)</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--mute:#5d6470;--line:#d9dde3;--blue:#1f5fd1;--blueink:#fff;
--warnbg:#fff4d6;--errbg:#fde2e2;--ok:#1e8e3e}
@media (prefers-color-scheme:dark){:root{--bg:#121417;--card:#1c1f24;--ink:#eceef1;--mute:#9aa2ad;--line:#333841;
--blue:#6ea0ff;--blueink:#0b0d10;--warnbg:#3a3214;--errbg:#3d1d1d}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body{overflow-x:hidden}
.wrap{max-width:720px;margin:0 auto;padding:0 16px 48px}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px}
header .in{max-width:720px;margin:0 auto;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
#progress{font-weight:700;font-size:17px;flex:1;min-width:0}
button,.btn{font:inherit;cursor:pointer;border-radius:12px;border:2px solid var(--line);background:var(--card);color:var(--ink);
min-height:48px;padding:8px 12px;touch-action:manipulation;-webkit-tap-highlight-color:transparent;text-decoration:none;
display:inline-flex;align-items:center;justify-content:center;text-align:center}
button:active,.btn:active{transform:scale(.98)}
#dl{font-weight:700;border-color:var(--blue);color:var(--blue)}
.banner{margin:12px 0;padding:12px 14px;border-radius:10px;font-weight:600;display:none}
.banner.show{display:block}.warn{background:var(--warnbg)}.err{background:var(--errbg)}
details{margin:12px 0;background:var(--card);border:1px solid var(--line);border-radius:12px}
summary{padding:12px 14px;font-weight:700;cursor:pointer;min-height:48px;display:flex;align-items:center}
details ul{margin:0;padding:0 14px 12px 32px}details li{margin:4px 0}details p{margin:0;padding:0 14px 12px}
.crit{white-space:pre-wrap;font:14px/1.45 ui-monospace,Menlo,Consolas,monospace;padding:0 14px 14px;overflow-wrap:anywhere}
.crit .stp{display:block;margin-top:14px;font-size:15px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}
.meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;color:var(--mute);font-size:14px}
.rid{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:700;color:var(--ink);font-size:15px}
h1{font-size:19px;margin:8px 0 0;overflow-wrap:anywhere}
.saved{margin-top:10px;font-weight:700;padding:8px 10px;border-radius:8px;border:2px solid var(--ok);color:var(--ok)}
.links{display:flex;gap:10px;flex-wrap:wrap}
.lk{min-height:64px;font-weight:700;font-size:18px;border-color:var(--blue);color:var(--blue);flex:2 1 220px}
.lk.small{min-height:48px;font-size:15px;flex:1 1 110px}
.grp{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:12px 0}
.grp.miss{border-color:#c62828;box-shadow:0 0 0 2px #c62828}
.grp h2{font-size:16px;margin:0 0 2px}.grp .q{color:var(--mute);font-size:14px;margin:0 0 10px}
.opts{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.opts.two{grid-template-columns:1fr 1fr}
.opts button{flex-direction:column;gap:2px;font-weight:700;min-height:60px}
.opts button small{font-weight:500;font-size:12px;color:var(--mute)}
.opts button.on{background:var(--blue);border-color:var(--blue);color:var(--blueink)}
.opts button.on small{color:var(--blueink);opacity:.85}
.opts button:disabled{opacity:.4}
.sub{margin-top:12px;padding-top:10px;border-top:1px dashed var(--line)}
.sub .t{font-size:14px;font-weight:600;margin-bottom:8px}
input[type=text],textarea{width:100%;font:inherit;padding:10px 12px;border-radius:12px;border:2px solid var(--line);background:var(--card);color:var(--ink)}
textarea{resize:vertical;min-height:84px}
label{display:block;font-size:14px;font-weight:600;margin:10px 0 4px}
#save{width:100%;min-height:68px;font-size:20px;font-weight:800;background:var(--blue);border-color:var(--blue);color:var(--blueink);margin-top:6px}
#need{min-height:22px;margin:8px 0 0;color:#c62828;font-weight:600;text-align:center}
.row{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:14px}
.row button{font-size:15px}
.tools{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}
#toast{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);max-width:calc(100% - 32px);background:var(--ink);color:var(--bg);
padding:12px 16px;border-radius:10px;font-weight:600;opacity:0;transition:opacity .2s;pointer-events:none;z-index:9}
#toast.show{opacity:1}
.done{text-align:center;font-size:20px;font-weight:700;padding:24px 0}
.hint{color:var(--mute);font-size:13px;margin-top:14px;text-align:center}
</style>
</head>
<body>
<header><div class="in">
  <div id="progress">…</div>
  <button id="dl" type="button">Download decisions</button>
</div></header>
<div class="wrap">
  <div id="storeErr" class="banner err">Browser storage is unavailable or failing. Your answers are kept only while this tab stays open. Use “Download decisions” often.</div>
  <div id="ckpt" class="banner warn"></div>

  <details>
    <summary>Quick guide (plain wording)</summary>
    <ul>
      <li>Open the paper and find the <b>one</b> memory / context / information-handling mechanism it presents as its contribution (stored, kept, removed, compressed, retrieved or supplied to the model).</li>
      <li><b>Scope</b>: where does the information that mechanism gives the agent come from?
        <b>WITHIN</b> = made during this one task. <b>CROSS</b> = made by earlier, separate tasks (by the agent, other agents or humans). <b>EXTERNAL</b> = not made by running tasks (docs, a fixed knowledge base, web search, a code index). <b>NOT APPLICABLE</b> = no mechanism, or it works by changing the model's weights, or it is about human-written instruction files.</li>
      <li>If it mixes sources: CROSS if any part is CROSS, else EXTERNAL if any part is EXTERNAL, else WITHIN. Words like “memory” or “experience” decide nothing; look at what is stored, when it is made and when it is used.</li>
      <li><b>Role</b>: CORE if the mechanism is in the paper’s own list of contributions (or the abstract’s “we propose …”). COMPONENT if it is a part of something else the paper claims.</li>
      <li><b>Activity</b>: the kind of task it is tested on.</li>
      <li>Use only the paper’s own text. The reasoning box is optional; one line is enough. The exact criteria are in the box below.</li>
    </ul>
  </details>
  <details>
    <summary>Criteria (exact text from the prompt)</summary>
    <div class="crit">__CRITERIA__</div>
  </details>

  <div id="paper" class="card"></div>
  <div id="links" class="links"></div>

  <div id="form">
    <section class="grp" id="grp-scope">
      <h2>1. Reuse scope</h2>
      <p class="q">Where does the information the mechanism gives the agent come from?</p>
      <div class="opts" data-field="scope">
        <button type="button" data-v="WITHIN">WITHIN<small>this task only</small></button>
        <button type="button" data-v="CROSS">CROSS<small>earlier, separate tasks</small></button>
        <button type="button" data-v="EXTERNAL">EXTERNAL<small>docs, fixed KB, code index</small></button>
        <button type="button" data-v="NOT_APPLICABLE">NOT APPLICABLE<small>give a reason</small></button>
      </div>
      <div class="sub" id="sub-na" hidden>
        <div class="t">Reason</div>
        <div class="opts" data-field="na_reason">
          <button type="button" data-v="NO_MECHANISM">NO_MECHANISM<small>none to identify</small></button>
          <button type="button" data-v="PARAMETRIC">PARAMETRIC<small>changes model weights</small></button>
          <button type="button" data-v="CONTEXT_FILES">CONTEXT_FILES<small>AGENTS.md-style files</small></button>
        </div>
      </div>
      <div class="sub" id="sub-origin" hidden>
        <div class="t">Whose earlier tasks?</div>
        <div class="opts" data-field="cross_origin">
          <button type="button" data-v="own_trajectories">Own<small>this system’s earlier tasks</small></button>
          <button type="button" data-v="others_tasks">Others’<small>humans or other agents</small></button>
          <button type="button" data-v="both">Both</button>
        </div>
      </div>
    </section>

    <section class="grp" id="grp-role">
      <h2>2. Role</h2>
      <p class="q" id="roleq">Is the mechanism itself a stated contribution?</p>
      <div class="opts two" data-field="role">
        <button type="button" data-v="CORE">CORE<small>in the contribution claim</small></button>
        <button type="button" data-v="COMPONENT">COMPONENT<small>part of a bigger system</small></button>
      </div>
    </section>

    <section class="grp" id="grp-activity">
      <h2>3. SE activity</h2>
      <p class="q">What kind of task is it applied to?</p>
      <div class="opts" data-field="activity">
        <button type="button" data-v="REQUIREMENTS_ENGINEERING">Requirements engineering</button>
        <button type="button" data-v="SOFTWARE_DESIGN">Software design</button>
        <button type="button" data-v="SOFTWARE_DEVELOPMENT">Software development<small>code generation, completion, translation</small></button>
        <button type="button" data-v="QUALITY_ASSURANCE">Quality assurance<small>testing, fault localisation, vulnerabilities</small></button>
        <button type="button" data-v="SOFTWARE_MAINTENANCE">Software maintenance<small>issue resolution, repair, refactoring</small></button>
        <button type="button" data-v="SOFTWARE_MANAGEMENT">Software management</button>
      </div>
    </section>

    <section class="grp">
      <h2>Optional</h2>
      <label for="mechanism">Mechanism (a few words)</label>
      <input id="mechanism" type="text" autocomplete="off">
      <label for="reasoning">Reasoning</label>
      <textarea id="reasoning" rows="3" placeholder="Why this scope / role? One line is enough."></textarea>
    </section>

    <button id="save" type="button">Save &amp; next</button>
    <div id="need"></div>
  </div>

  <div class="row">
    <button id="back" type="button">◀ Back</button>
    <button id="jump" type="button">Jump to #</button>
    <button id="again" type="button">Open paper again</button>
  </div>
  <div class="tools">
    <button id="imp" type="button">Import decisions</button>
    <button id="dl2" type="button">Download decisions</button>
  </div>
  <input id="file" type="file" accept=".csv,text/csv" hidden>
  <div class="hint">Answers are saved in this browser. Download the CSV when you finish (it downloads by itself after the last paper).</div>
</div>
<div id="toast"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
"use strict";
const DATA = JSON.parse(document.getElementById("data").textContent);
const P = DATA.papers, N = P.length;
const PREFIX = "class_review_v1_", KEY = PREFIX + DATA.hash;
const IDX = new Map(P.map((p, i) => [p.id, i]));
const ALLOWED = {
  scope: ["WITHIN", "CROSS", "EXTERNAL", "NOT_APPLICABLE"],
  na_reason: ["NO_MECHANISM", "PARAMETRIC", "CONTEXT_FILES"],
  cross_origin: ["own_trajectories", "others_tasks", "both"],
  role: ["CORE", "COMPONENT"],
  activity: ["REQUIREMENTS_ENGINEERING", "SOFTWARE_DESIGN", "SOFTWARE_DEVELOPMENT", "QUALITY_ASSURANCE", "SOFTWARE_MAINTENANCE", "SOFTWARE_MANAGEMENT"],
};
const PICK = ["scope", "na_reason", "cross_origin", "role", "activity"];
const TEXT = ["mechanism", "reasoning"];
const COLS = ["record_id", "scope", "na_reason", "cross_origin", "role", "activity", "mechanism", "reasoning", "decided_at", "position"];
const $ = id => document.getElementById(id);

let state = { decisions: {} };
let cur = 0, lockUntil = 0, form = blank();

function blank() { return { scope: "", na_reason: "", cross_origin: "", role: "", activity: "", mechanism: "", reasoning: "" }; }

// ---------- storage (every call guarded; falls back to memory) ----------
function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
function readStored(k) { try { const s = JSON.parse(lsGet(k) || "null"); return s && typeof s === "object" ? s : null; } catch (e) { return null; } }
const t = d => { const x = Date.parse(d && d.decided_at); return isNaN(x) ? -Infinity : x; };
function validDecision(d) {
  if (!d || !ALLOWED.scope.includes(d.scope)) return false;
  for (const f of ["na_reason", "cross_origin", "role", "activity"]) if (d[f] && !ALLOWED[f].includes(d[f])) return false;
  return true;
}
function mergeDecisions(dst, src) {   // a src entry wins only if strictly newer
  let n = 0;
  for (const id in src || {}) {
    const d = src[id];
    if (!IDX.has(id) || !validDecision(d)) continue;
    if (!dst[id] || t(d) > t(dst[id])) { dst[id] = { ...blank(), ...d, position: IDX.get(id) + 1 }; n++; }
  }
  return n;
}
function save() {
  const other = readStored(KEY);
  if (other) mergeDecisions(state.decisions, other.decisions);   // never clobber another open tab
  const s = JSON.stringify(state);
  const ok = lsSet(KEY, s) && lsGet(KEY) === s;
  $("storeErr").classList.toggle("show", !ok);
  return ok;
}
function load() {
  const s = readStored(KEY);
  if (s) mergeDecisions(state.decisions, s.decisions);
  const probe = PREFIX + "probe";
  $("storeErr").classList.toggle("show", !(lsSet(probe, "1") && lsGet(probe) === "1"));
  try { localStorage.removeItem(probe); } catch (e) {}
}
window.addEventListener("storage", e => {
  if (e.key !== KEY) return;
  const o = readStored(KEY);
  if (o && mergeDecisions(state.decisions, o.decisions)) renderTop();
});

// ---------- navigation ----------
const done = i => !!state.decisions[P[i].id];
function firstUnrated() { for (let i = 0; i < N; i++) if (!done(i)) return i; return N; }
function nextUnrated(from) {
  for (let i = from + 1; i < N; i++) if (!done(i)) return i;
  for (let i = 0; i < from && i < N; i++) if (!done(i)) return i;
  return N;
}
function go(i) {
  cur = Math.max(0, Math.min(N, i));
  const d = cur < N ? state.decisions[P[cur].id] : null;
  form = d ? { ...blank(), ...d } : blank();
  $("need").textContent = "";
  render();
  window.scrollTo(0, 0);
}
function openUrl(url) {
  if (!url) return;
  const w = window.open(url, "_blank");
  if (w) { try { w.opener = null; } catch (e) {} }
  else toast("Popup blocked - tap the Open paper (PDF) button", 4000);
}

// ---------- form ----------
const noMech = () => form.scope === "NOT_APPLICABLE" && form.na_reason === "NO_MECHANISM";
function setPick(field, v) {
  form[field] = form[field] === v ? "" : v;
  if (form.scope !== "NOT_APPLICABLE") form.na_reason = "";
  if (form.scope !== "CROSS") form.cross_origin = "";
  if (noMech()) form.role = "";
  renderForm();
}
function missing() {
  const m = [];
  if (!form.scope) m.push("scope");
  if (form.scope === "NOT_APPLICABLE" && !form.na_reason) m.push("reason");
  if (form.scope === "CROSS" && !form.cross_origin) m.push("whose earlier tasks");
  if (!noMech() && !form.role) m.push("role");
  if (!form.activity) m.push("activity");
  return m;
}
function renderForm() {
  for (const g of document.querySelectorAll(".opts[data-field]")) {
    const f = g.dataset.field;
    for (const b of g.querySelectorAll("button")) b.classList.toggle("on", form[f] === b.dataset.v);
  }
  $("sub-na").hidden = form.scope !== "NOT_APPLICABLE";
  $("sub-origin").hidden = form.scope !== "CROSS";
  for (const b of document.querySelectorAll('[data-field="role"] button')) b.disabled = noMech();
  $("roleq").textContent = noMech() ? "No mechanism, so no role." : "Is the mechanism itself a stated contribution?";
  for (const f of TEXT) if ($(f).value !== form[f]) $(f).value = form[f];
  for (const g of document.querySelectorAll(".grp")) g.classList.remove("miss");
}

// ---------- render ----------
function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function renderTop() {
  $("progress").textContent = `${Object.keys(state.decisions).length} / ${N} done`;
}
function render() {
  renderTop();
  const paper = $("paper"), links = $("links");
  paper.innerHTML = ""; links.innerHTML = "";
  const end = cur >= N;
  $("form").hidden = end; $("again").disabled = end;
  if (end) {
    const left = N - Object.keys(state.decisions).length;
    paper.append(el("div", "done", left ? `End of list - ${left} still to do (use Jump to #)` : `All ${N} papers done 🎉`));
    paper.append(el("div", "hint", "Press Download decisions to save the CSV."));
    return;
  }
  const p = P[cur], d = state.decisions[p.id];
  const meta = el("div", "meta");
  meta.append(el("span", "rid", p.id), el("span", "", `#${cur + 1} of ${N}`));
  paper.append(meta, el("h1", "", p.title));
  if (d) paper.append(el("div", "saved", "Already saved - change anything and press Save to overwrite"));
  p.links.forEach((l, i) => {
    const a = el("a", "btn lk" + (i ? " small" : ""), l.label + " ↗");
    a.href = l.url; a.target = "_blank"; a.rel = "noopener";
    links.append(a);
  });
  renderForm();
}

function saveAndNext() {
  if (cur >= N || Date.now() < lockUntil) return;
  const miss = missing();
  if (miss.length) {
    $("need").textContent = "Still needed: " + miss.join(", ");
    $("grp-scope").classList.toggle("miss", miss.some(m => ["scope", "reason", "whose earlier tasks"].includes(m)));
    $("grp-role").classList.toggle("miss", miss.includes("role"));
    $("grp-activity").classList.toggle("miss", miss.includes("activity"));
    return;
  }
  lockUntil = Date.now() + 700;   // stops an accidental double tap saving two papers
  const p = P[cur];
  const d = { ...form };
  for (const f of TEXT) d[f] = (d[f] || "").trim();
  d.decided_at = new Date().toISOString(); d.position = cur + 1;
  state.decisions[p.id] = d;
  const nxt = nextUnrated(cur);
  const ok = save();
  if (nxt < N) openUrl(P[nxt].links[0].url);   // same click => not popup-blocked
  go(nxt);
  toast(`${ok ? "Saved" : "Saved in memory only"}: ${p.id}`);
  if (Object.keys(state.decisions).length === N) {
    const name = download();
    const b = $("ckpt");
    b.textContent = `All ${N} done. Downloaded ${name}. Keep it safe.`;
    b.classList.add("show");
  }
}

// ---------- CSV ----------
const q = v => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
function buildCSV() {
  const lines = [COLS.map(q).join(",")];
  const ids = Object.keys(state.decisions).sort((a, b) => IDX.get(a) - IDX.get(b));
  for (const id of ids) {
    const d = state.decisions[id];
    lines.push(COLS.map(c => c === "record_id" ? id : c === "position" ? IDX.get(id) + 1 : d[c]).map(q).join(","));
  }
  return "\ufeff" + lines.join("\r\n") + "\r\n";
}
function download() {
  const n = Object.keys(state.decisions).length;
  const dt = new Date(), z = x => String(x).padStart(2, "0");
  const stamp = `${dt.getFullYear()}${z(dt.getMonth() + 1)}${z(dt.getDate())}-${z(dt.getHours())}${z(dt.getMinutes())}`;
  const name = `class_decisions_${n}_${stamp}.csv`;
  const url = URL.createObjectURL(new Blob([buildCSV()], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url; a.download = name; a.style.display = "none";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
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
  for (const k of ["record_id", "scope", "decided_at"]) if (ix(k) < 0) throw new Error("missing column " + k);
  const src = {}; let unknown = 0, bad = 0;
  for (const r of rows.slice(1)) {
    if (r.length === 1 && r[0] === "") continue;
    const id = (r[ix("record_id")] || "").trim();
    if (!IDX.has(id)) { unknown++; continue; }
    const d = { ...blank(), decided_at: (r[ix("decided_at")] || "").trim() };
    for (const c of [...PICK, ...TEXT]) if (ix(c) >= 0) d[c] = (r[ix(c)] || "").trim();
    if (!validDecision(d) || isNaN(Date.parse(d.decided_at))) { bad++; continue; }
    if (!src[id] || t(d) > t(src[id])) src[id] = d;
  }
  const changed = mergeDecisions(state.decisions, src);
  const ok = save();
  go(firstUnrated());
  return `Imported: ${changed} new/updated, ${Object.keys(src).length - changed} already up to date` +
    (unknown ? `, ${unknown} unknown record_ids skipped` : "") + (bad ? `, ${bad} bad rows skipped` : "") +
    (ok ? "" : " (storage failing - kept in memory)");
}

let toastTimer;
function toast(msg, ms = 1800) {
  const e = $("toast"); e.textContent = msg; e.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => e.classList.remove("show"), ms);
}

// ---------- wiring ----------
for (const g of document.querySelectorAll(".opts[data-field]"))
  for (const b of g.querySelectorAll("button")) b.addEventListener("click", () => setPick(g.dataset.field, b.dataset.v));
for (const f of TEXT) $(f).addEventListener("input", () => { form[f] = $(f).value; });
$("save").onclick = saveAndNext;
$("back").onclick = () => go(cur - 1);
$("again").onclick = () => { if (cur < N) openUrl(P[cur].links[0].url); };
$("jump").onclick = () => {
  const s = prompt(`Go to # (1-${N})`, String(Math.min(cur + 1, N)));
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

load();
go(firstUnrated());
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

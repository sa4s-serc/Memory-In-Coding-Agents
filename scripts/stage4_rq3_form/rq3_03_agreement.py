"""Step 3. Agreement between the two LLMs, the stratified sample for human evaluation,
and the adjudication sheet for the decisions on which the two LLMs disagree.

Output: results/llm_agreement.json, results/disagreements.csv
        results/human_sample.csv              the sampled papers and their stratum
        results/human_eval.xlsx               blind sheet for the human evaluator (no LLM output in it)
        results/adjudication.xlsx             one row per disagreement, with both models' quotes
Do the human evaluation BEFORE opening adjudication.xlsx.
"""
import json
import random

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

from rq3_common import MODELS, N_HUMAN, OUT, SEED_HUMAN, field_ids, form, kappa, load_llm, to_vector

F = field_ids()
fname = {f["id"]: f["name"] for f in form()["fields"]}
papers = pd.read_csv(OUT / "papers.csv")
A, B = load_llm("A"), load_llm("B")
missing = [r for r in papers.record_id if r not in A or r not in B]
if missing:
    raise SystemExit(f"{len(missing)} papers lack output from one model: {missing[:10]}")

rows, dis = [], []
for rid, scope, pilot in zip(papers.record_id, papers.scope, papers.pilot):
    va, vb = to_vector(A[rid]), to_vector(B[rid])
    for f in F:
        rows.append((rid, scope, pilot, f, va[f], vb[f]))
        if va[f] != vb[f]:
            q = lambda res: " | ".join(f"p.{e.get('page')}: {e.get('quote', '')}"
                                       for e in res["fields"][f].get("evidence", []))
            dis.append({"record_id": rid, "scope": scope, "field": f"{f} {fname[f]}",
                        "model_A": va[f], "quotes_A": q(A[rid]), "model_B": vb[f], "quotes_B": q(B[rid]),
                        "final": "", "note": ""})
m = pd.DataFrame(rows, columns=["record_id", "scope", "pilot", "field", "A", "B"])
k, po = kappa(m.A, m.B)
per = {}
for f in F:
    s = m[m.field == f]
    kf, pf = kappa(s.A, s.B)
    per[f] = {"kappa": None if kf is None else round(kf, 3), "agreement": round(pf, 3),
              "A": int(s.A.sum()), "B": int(s.B.sum())}
res = {"models": MODELS, "papers": int(papers.shape[0]), "decisions": int(len(m)),
       "pooled_kappa": round(k, 3), "pooled_agreement": round(po, 3),
       "disagreements": len(dis), "papers_with_disagreement": int(m[m.A != m.B].record_id.nunique()),
       "per_field": per}
(OUT / "llm_agreement.json").write_text(json.dumps(res, indent=1))
pd.DataFrame(dis).to_csv(OUT / "disagreements.csv", index=False)

# --- stratified sample (non-pilot papers): scope x (any disagreement or not), proportional, >= 3 per stratum
dpapers = set(m[m.A != m.B].record_id)
pool = papers[papers.pilot == 0].copy()
pool["stratum"] = pool.scope + "/" + pool.record_id.map(lambda r: "disagree" if r in dpapers else "agree")
sizes = pool.stratum.value_counts().sort_index()
alloc = {s: max(min(3, n), round(N_HUMAN * n / len(pool))) for s, n in sizes.items()}
while sum(alloc.values()) > N_HUMAN:
    s = max(alloc, key=lambda x: alloc[x] - N_HUMAN * sizes[x] / len(pool))
    alloc[s] -= 1
while sum(alloc.values()) < N_HUMAN:
    s = min(alloc, key=lambda x: alloc[x] - N_HUMAN * sizes[x] / len(pool))
    alloc[s] += 1
rng = random.Random(SEED_HUMAN)
sample = []
for s in sorted(alloc):
    ids = sorted(pool[pool.stratum == s].record_id)
    sample += [(r, s) for r in sorted(rng.sample(ids, min(alloc[s], len(ids))))]
hs = pd.DataFrame(sample, columns=["record_id", "stratum"])
hs.to_csv(OUT / "human_sample.csv", index=False)


def write(dest, sheets, widths):
    if dest.exists():
        print(f"{dest.name} exists, not overwritten")
        return
    with pd.ExcelWriter(dest, engine="openpyxl") as w:
        for name, df in sheets:
            df.to_excel(w, sheet_name=name, index=False)
    wb = load_workbook(dest)
    for name, wd in widths.items():
        ws = wb[name]
        for col, v in wd.items():
            ws.column_dimensions[col].width = v
        for c in ws[1]:
            c.font = Font(bold=True)
            c.alignment = Alignment(wrap_text=True, vertical="top")
        for r in ws.iter_rows(min_row=2):
            for c in r:
                c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "B2"
    wb.save(dest)


fl = form()
fields_sheet = pd.DataFrame([{"field": f"{f['id']} {f['name']}", "group": f["group"], "definition": f["definition"],
                              "includes": "\n".join(f"- {i['item']}: {i['description']}" for i in f["includes"])}
                             for f in fl["fields"]])
instr = pd.DataFrame({"Instructions": [
    "Read each sampled paper (PDF, or results/text/<record_id>.txt) and fill in the extraction form yourself.",
    "For each field enter 1 if the authors state at least one limitation of that kind about their own work, else 0.",
    *[f"Rule {i}: {r}" for i, r in enumerate(fl["rules"], 1)],
    "If the only limitation statements are boilerplate, enter 1 in only_boilerplate and 0 in every field.",
    "If the paper states no limitation, enter 1 in no_limitation and 0 in every field.",
    "Do not look at the LLM output, disagreements.csv or adjudication.xlsx before finishing this sheet."]})
cols = [f"{f} {fname[f]}" for f in F]
he = pd.DataFrame([{"record_id": r, **{c: "" for c in cols}, "only_boilerplate": "", "no_limitation": "", "note": ""}
                   for r in hs.record_id])
write(OUT / "human_eval.xlsx", [("instructions", instr), ("form", he), ("fields", fields_sheet)],
      {"instructions": {"A": 120}, "form": {"A": 10, **{chr(66 + i): 12 for i in range(13)}},
       "fields": {"A": 30, "C": 60, "D": 90}})
write(OUT / "adjudication.xlsx", [("disagreements", pd.DataFrame(dis, columns=[
    "record_id", "scope", "field", "model_A", "quotes_A", "model_B", "quotes_B", "final", "note"])),
    ("fields", fields_sheet)],
      {"disagreements": {"A": 10, "C": 24, "E": 60, "G": 60, "H": 7, "I": 25},
       "fields": {"A": 30, "C": 60, "D": 90}})

print("=== RQ3 LLM AGREEMENT ===")
print(f"A = {MODELS['A']}, B = {MODELS['B']}")
print(f"{res['papers']} papers x {len(F)} fields = {res['decisions']} decisions; "
      f"pooled kappa {k:.3f}, agreement {po:.1%}")
print(f"disagreements {len(dis)} in {res['papers_with_disagreement']} papers")
for f in F:
    p = per[f]
    print(f"{f} {fname[f]}: kappa {p['kappa']}, agree {p['agreement']:.0%}, A {p['A']} / B {p['B']}")
print("human sample:", {k: int(v) for k, v in hs.stratum.value_counts().sort_index().items()})

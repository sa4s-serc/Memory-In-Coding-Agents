"""Step 4. Final field values per paper: the value both LLMs agree on, otherwise the
adjudicated value from adjudication.xlsx. Counts per field.

Output: results/paper_fields.csv, results/rq3_summary.json
Prints a summary.
"""
import json

import pandas as pd

from rq3_common import OUT, field_ids, form, load_llm, to_vector

F = field_ids()
fl = form()
fname = {f["id"]: f["name"] for f in fl["fields"]}
fgroup = {f["id"]: f["group"] for f in fl["fields"]}
groups = list(dict.fromkeys(fgroup.values()))
papers = pd.read_csv(OUT / "papers.csv")
A, B = load_llm("A"), load_llm("B")

adj = pd.read_excel(OUT / "adjudication.xlsx", sheet_name="disagreements")
adj["fid"] = adj.field.astype(str).str.split(" ").str[0]
adj["final"] = pd.to_numeric(adj.final, errors="coerce")
if adj.final.isna().any() or not adj.final.isin([0, 1]).all():
    raise SystemExit(f"adjudication.xlsx: {int(adj.final.isna().sum())} rows without a final value (0 or 1)")
adjd = {(r, f): int(v) for r, f, v in zip(adj.record_id, adj.fid, adj.final)}

rows = []
for rid, scope, role, pilot in zip(papers.record_id, papers.scope, papers.role, papers.pilot):
    va, vb = to_vector(A[rid]), to_vector(B[rid])
    final = {f: va[f] if va[f] == vb[f] else adjd[(rid, f)] for f in F}
    nolim = bool(A[rid].get("no_limitation")) and bool(B[rid].get("no_limitation"))
    boiler = bool(A[rid].get("only_boilerplate")) and bool(B[rid].get("only_boilerplate"))
    status = "limitations" if any(final.values()) else "only_boilerplate" if boiler else "none" if nolim else "none_or_boilerplate"
    rows.append({"record_id": rid, "scope": scope, "role": role, "pilot": pilot, **final,
                 "n_fields": sum(final.values()), "status": status})
pf = pd.DataFrame(rows)
pf.to_csv(OUT / "paper_fields.csv", index=False)


def counts(df):
    return {"n": len(df), "with_limitations": int((df.n_fields > 0).sum()),
            "without": int((df.n_fields == 0).sum()),
            "fields": {f: int(df[f].sum()) for f in F},
            "groups": {g: int((df[[f for f in F if fgroup[f] == g]].sum(axis=1) > 0).sum()) for g in groups},
            "median_fields_if_any": float(df[df.n_fields > 0].n_fields.median()) if (df.n_fields > 0).any() else 0.0}


s = {"all": counts(pf), "WITHIN": counts(pf[pf.scope == "WITHIN"]), "CROSS": counts(pf[pf.scope == "CROSS"]),
     "adjudicated": len(adjd), "adjudicated_to_1": int(sum(adjd.values()))}
(OUT / "rq3_summary.json").write_text(json.dumps(s, indent=1))

a, w, c = s["all"], s["WITHIN"], s["CROSS"]
print("=== RQ3 FINAL ===")
print(f"papers all {a['n']} | within {w['n']} | cross {c['n']}; adjudicated decisions {len(adjd)} "
      f"(set to 1: {s['adjudicated_to_1']})")
print(f"with at least one field: {a['with_limitations']} (W {w['with_limitations']}, C {c['with_limitations']}); "
      f"none: {a['without']} (W {w['without']}, C {c['without']})")
print("field | all | within | cross")
for f in F:
    print(f"{f} {fname[f]} | {a['fields'][f]} | {w['fields'][f]} | {c['fields'][f]}")
for g in groups:
    print(f"group {g} | {a['groups'][g]} | {w['groups'][g]} | {c['groups'][g]}")
print(f"median fields per paper (papers with any): all {a['median_fields_if_any']}, "
      f"W {w['median_fields_if_any']}, C {c['median_fields_if_any']}")

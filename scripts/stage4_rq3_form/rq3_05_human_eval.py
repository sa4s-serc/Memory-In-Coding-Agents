"""Step 5. Compare the human evaluation with each LLM and with the final values,
on the stratified sample (papers x 11 fields, pooled; and per field).
Pooled kappa gets a 95% bootstrap CI (papers resampled, 5000 draws, seed 1). Per field: counts
(human / other / both), kappa, raw agreement and PABAK (2 x agreement - 1), which is not
distorted by fields that are very rare or very common.

Output: results/human_eval.json; prints a summary.
"""
import json

import numpy as np
import pandas as pd

from rq3_common import MODELS, OUT, field_ids, form, kappa, load_llm, to_vector

F = field_ids()
fname = {f["id"]: f["name"] for f in form()["fields"]}
hs = pd.read_csv(OUT / "human_sample.csv")
h = pd.read_excel(OUT / "human_eval.xlsx", sheet_name="form").set_index("record_id")
h.columns = [str(c).split(" ")[0] for c in h.columns]
h = h.loc[hs.record_id, F]
if h.isna().any().any():
    raise SystemExit(f"human_eval.xlsx has empty cells for: {h[h.isna().any(axis=1)].index.tolist()}")
h = h.astype(int)
A, B = load_llm("A"), load_llm("B")
pf = pd.read_csv(OUT / "paper_fields.csv").set_index("record_id")


def compare(other, ids, ref):
    X = np.array([[int(ref.loc[r, f]) for f in F] for r in ids])
    Y = np.array([[int(other(r)[f]) for f in F] for r in ids])
    k, po = kappa(X.ravel(), Y.ravel())
    tp = int((X & Y).sum())
    rng = np.random.default_rng(1)
    boot = [kappa(X[i].ravel(), Y[i].ravel())[0] for i in (rng.integers(0, len(ids), len(ids)) for _ in range(5000))]
    boot = [b for b in boot if b is not None]
    per = {}
    for j, f in enumerate(F):
        kf, pf_ = kappa(X[:, j], Y[:, j])
        per[f] = {"human": int(X[:, j].sum()), "other": int(Y[:, j].sum()), "both": int((X[:, j] & Y[:, j]).sum()),
                  "kappa": None if kf is None else round(kf, 3), "agreement": round(pf_, 3), "pabak": round(2 * pf_ - 1, 3)}
    return {"kappa": round(k, 3), "kappa_ci95": [round(float(np.percentile(boot, 2.5)), 3), round(float(np.percentile(boot, 97.5)), 3)],
            "agreement": round(po, 3), "precision": round(tp / max(1, int(Y.sum())), 3),
            "recall": round(tp / max(1, int(X.sum())), 3), "human_fields": int(X.sum()), "other_fields": int(Y.sum()),
            "per_field": per}


ids = list(hs.record_id)
res = {"sample": len(ids), "decisions": len(ids) * len(F),
       "human_vs_A": compare(lambda r: to_vector(A[r]), ids, h),
       "human_vs_B": compare(lambda r: to_vector(B[r]), ids, h),
       "human_vs_final": compare(lambda r: pf.loc[r, F].to_dict(), ids, h)}

(OUT / "human_eval.json").write_text(json.dumps(res, indent=1))

print("=== RQ3 HUMAN EVALUATION ===")
print(f"stratified sample {len(ids)} papers x {len(F)} fields = {len(ids) * len(F)} decisions; "
      f"strata { {k: int(v) for k, v in hs.stratum.value_counts().sort_index().items()} }")
for key, lab in [("human_vs_A", f"A {MODELS['A']}"), ("human_vs_B", f"B {MODELS['B']}"), ("human_vs_final", "final")]:
    r = res[key]
    print(f"{lab}: kappa {r['kappa']} (95% CI {r['kappa_ci95'][0]}-{r['kappa_ci95'][1]}), agreement {r['agreement']:.1%}, "
          f"precision {r['precision']:.2f}, recall {r['recall']:.2f}")
print("per field, human vs final:")
for f in F:
    p = res["human_vs_final"]["per_field"][f]
    print(f"  {f} {fname[f]}: human {p['human']}, final {p['other']}, both {p['both']}; "
          f"kappa {p['kappa']}, agree {p['agreement']:.0%}, PABAK {p['pabak']}")

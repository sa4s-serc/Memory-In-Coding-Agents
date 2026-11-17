#!/usr/bin/env python3
"""Compute Stage 1 agreement from the two filled labelling sheets.

  python compute_stage1_kappa.py
  python compute_stage1_kappa.py --raters PSK,Aviral

Step 1 (first run): Cohen's kappa between the two raters. Disagreements are written to
  stage1_disagreements.xlsx with an empty 'consensus' column.
  
Step 2 (after you fill 'consensus' together): rerun. The script builds consensus labels and
  reports the model against them: kappa on the sample, precision, and recall weighted by
  band size (the sample is stratified, so unweighted recall would be biased).
  
Results are printed and written to stage1_validation_results.txt.
"""
import argparse, os, sys
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

LABELS = ("INCLUDE", "EXCLUDE")


def read_labels(path):
    ws = load_workbook(path, read_only=True)["labels"]
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h).strip() for h in rows[0]]
    i_id, i_dec = head.index("sample_id"), head.index("decision")
    out, blank, bad = {}, [], []
    for r in rows[1:]:
        sid = str(r[i_id]).strip() if r[i_id] else ""
        if not sid:
            continue
        d = str(r[i_dec] or "").strip().upper()
        if not d:
            blank.append(sid)
        elif d not in LABELS:
            bad.append((sid, d))
        out[sid] = d
    if blank or bad:
        sys.exit(f"{path}: unlabelled {blank[:10]} invalid {bad[:10]}")
    return out


def read_key(path):
    ws = load_workbook(path, read_only=True)["key"]
    rows = list(ws.iter_rows(values_only=True))
    head = list(rows[0])
    return {r[0]: dict(zip(head, r)) for r in rows[1:] if r[0]}


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in LABELS)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe), po


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raters", default="PSK,Aviral")
    ap.add_argument("--key", default="stage1_sample_key.xlsx")
    a = ap.parse_args()
    r1, r2 = a.raters.split(",")
    L1, L2 = read_labels(f"stage1_labels_{r1}.xlsx"), read_labels(f"stage1_labels_{r2}.xlsx")
    key = read_key(a.key)
    if set(L1) != set(L2) or set(L1) != set(key):
        sys.exit("sample ids differ between the two sheets and the key")
    ids = sorted(key)
    out = []

    k, po = kappa([L1[i] for i in ids], [L2[i] for i in ids])
    dis = [i for i in ids if L1[i] != L2[i]]
    out.append(f"Inter-rater ({r1} vs {r2}), n={len(ids)}: kappa = {k:.3f}, "
               f"observed agreement = {po:.1%}, disagreements = {len(dis)}")

    dpath = "stage1_disagreements.xlsx"
    consensus = {i: L1[i] for i in ids if L1[i] == L2[i]}
    if dis and not os.path.exists(dpath):
        wb = Workbook(); ws = wb.active; ws.title = "resolve"
        ws.append(["sample_id", f"{r1}", f"{r2}", "consensus", "reason"])
        for c in ws[1]:
            c.font = Font(bold=True)
        for i in dis:
            ws.append([i, L1[i], L2[i], None, None])
        dv = DataValidation(type="list", formula1='"INCLUDE,EXCLUDE"', allow_blank=True)
        ws.add_data_validation(dv); dv.add(f"D2:D{len(dis) + 1}")
        ws.column_dimensions["E"].width = 60
        wb.save(dpath)
        out.append(f"Wrote {dpath}: resolve the {len(dis)} disagreements together, "
                   f"fill 'consensus', then rerun.")
    elif dis:
        ws = load_workbook(dpath, read_only=True)["resolve"]
        for r in list(ws.iter_rows(values_only=True))[1:]:
            if r[0] and r[3]:
                consensus[str(r[0]).strip()] = str(r[3]).strip().upper()
    todo = [i for i in ids if consensus.get(i) not in LABELS]

    if todo:
        out.append(f"Consensus missing for {len(todo)} records; model metrics not computed yet.")
    else:
        m = [key[i]["model_decision"] for i in ids]
        c = [consensus[i] for i in ids]
        km, pom = kappa(m, c)
        out.append(f"Model vs consensus, n={len(ids)}: kappa = {km:.3f}, "
                   f"observed agreement = {pom:.1%}")
        bands = {}
        for i in ids:
            b = key[i]["band"]
            s = bands.setdefault(b, {"N": int(key[i]["band_size"]), "n": 0, "inc": 0})
            s["n"] += 1
            s["inc"] += consensus[i] == "INCLUDE"
        est = {b: s["N"] * s["inc"] / s["n"] for b, s in bands.items()}
        for b in ("high", "mid", "low"):
            if b in bands:
                s = bands[b]
                out.append(f"  band {b:<4}: {s['inc']}/{s['n']} relevant in sample, "
                           f"estimated {est[b]:.0f} of {s['N']} in population")
        total = sum(est.values())
        prec = bands["high"]["inc"] / bands["high"]["n"]
        rec = est["high"] / total if total else float("nan")
        out.append(f"Precision of the retained set (score >= 0.70): {prec:.1%}")
        out.append(f"Recall at the 0.70 cutoff, weighted by band size: {rec:.1%} "
                   f"(estimated {est['high']:.0f} of {total:.0f} relevant records retained)")

    text = "\n".join(out)
    print(text)
    open("stage1_validation_results.txt", "w", encoding="utf-8").write(text + "\n")


if __name__ == "__main__":
    main()

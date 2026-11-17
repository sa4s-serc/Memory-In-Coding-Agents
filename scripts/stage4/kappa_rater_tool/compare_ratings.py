# /// script
# dependencies = ["openpyxl"]
# ///
"""Compare AG's decisions with the PSK classification and compute Cohen's kappa.

Usage:  uv run kappa_review/compare_ratings.py [CSV or glob ...] [--out kappa_comparison.xlsx]
Default glob: class_decisions_*.csv in the current directory. For each record_id the decision
with the latest decided_at wins. PSK_labelled_30.csv is only read here, after rating.
"""
import argparse
import csv
import glob
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent


def parse_time(s):
    try:
        t = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def read_rater(paths):
    best = {}
    for path in paths:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                rid, ts = (row.get("record_id") or "").strip(), parse_time(row.get("decided_at") or "")
                if rid and ts and (rid not in best or ts >= best[rid][0]):
                    best[rid] = (ts, row)
    return {rid: row for rid, (ts, row) in best.items()}


def kappa(a, b):
    """Return (observed agreement, kappa, approximate 95% CI). kappa is None if both raters never vary."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    if pe == 1:
        return po, None, None
    k = (po - pe) / (1 - pe)
    se = math.sqrt(po * (1 - po) / (n * (1 - pe) ** 2))
    return po, k, (k - 1.96 * se, k + 1.96 * se)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="*", default=["class_decisions_*.csv"])
    ap.add_argument("--out", default=str(HERE / "kappa_comparison.xlsx"))
    a = ap.parse_args()
    paths = sorted({p for pat in a.csvs for p in glob.glob(os.path.expanduser(pat))})
    if not paths:
        sys.exit(f"No CSV files match {a.csvs}")
    rater = read_rater(paths)
    psk = {r["record_id"]: r for r in csv.DictReader(open(HERE / "PSK_labelled_30.csv", encoding="utf-8-sig"))}
    titles = {r["record_id"]: r["title"] for r in csv.DictReader(open(HERE / "sample_30.csv", encoding="utf-8-sig"))}
    ids = [i for i in psk if i in rater]
    print(f"Rater decisions: {len(rater)}  compared: {len(ids)} of {len(psk)}")
    if len(ids) < len(psk):
        print("  not rated yet: " + ", ".join(i for i in psk if i not in rater))
    unknown = sorted(set(rater) - set(psk))
    if unknown:
        print("  record_ids in the CSV that are not in the sample: " + ", ".join(unknown))
    if not ids:
        sys.exit("Nothing to compare.")

    def scope_full(r):
        return r["scope"] if r["scope"] != "NOT_APPLICABLE" else "NA:" + (r["na_reason"] or "?")

    measures = {
        "scope, 4 groups (WITHIN / CROSS / EXTERNAL / NOT_APPLICABLE)": lambda r: r["scope"],
        "scope, NOT_APPLICABLE split by reason (6 groups)": scope_full,
        "CROSS vs everything else": lambda r: "CROSS" if r["scope"] == "CROSS" else "not CROSS",
        "role (CORE / COMPONENT / none)": lambda r: r["role"] or "none",
        "SE activity (6 groups)": lambda r: r["activity"] or "none",
    }
    print(f"\n{'measure':62} {'agree':>7} {'kappa':>7}  approx. 95% CI")
    for name, fn in measures.items():
        po, k, ci = kappa([fn(rater[i]) for i in ids], [fn(psk[i]) for i in ids])
        ks = "n/a" if k is None else f"{k:.2f}"
        cs = "" if ci is None else f"{max(ci[0], -1):.2f} to {min(ci[1], 1):.2f}"
        print(f"{name:62} {po:6.0%} {ks:>7}  {cs}")
    print(f"\nn = {len(ids)}. With so few papers the interval is wide and kappa is rough.")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "comparison"
    fields = ["scope", "na_reason", "cross_origin", "role", "activity", "mechanism"]
    head = ["record_id", "title"]
    for f in fields:
        head += [f"rater_{f}", f"ai_{f}"] + ([f"{f}_agree"] if f in ("scope", "na_reason", "role", "activity") else [])
    head.append("rater_reasoning")
    ws.append(head)
    for i in ids:
        row = [i, titles.get(i, "")]
        for f in fields:
            rv, av = (rater[i].get(f) or "").strip(), (psk[i].get(f) or "").strip()
            row += [rv, av] + (["yes" if rv == av else "NO"] if f in ("scope", "na_reason", "role", "activity") else [])
        row.append((rater[i].get("reasoning") or "").strip())
        ws.append(row)
    out = Path(a.out)
    tmp = out.with_name(out.name + ".tmp")
    wb.save(tmp)
    os.replace(tmp, out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

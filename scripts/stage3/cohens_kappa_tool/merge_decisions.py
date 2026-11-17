# /// script
# dependencies = ["openpyxl"]
# ///
"""Merge downloaded decision CSVs into a copy of impl_review.xlsx.

Usage:  uv run link_review/merge_decisions.py [CSV or glob ...] [--xlsx impl_review.xlsx] [--out impl_review_rated.xlsx]
Default glob: impl_decisions_*.csv in the current directory. impl_review.xlsx is never modified.
"""
import argparse
import csv
import glob
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
DECISIONS = ("GREEN", "ORANGE", "RED")
NEW_COLS = ("rating", "link_judged", "rating_note", "rated_at")


def parse_time(s):
    try:
        t = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def read_decisions(paths):
    best = {}
    for path in paths:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for n, row in enumerate(csv.DictReader(f), start=2):
                rid = (row.get("record_id") or "").strip()
                dec = (row.get("decision") or "").strip().upper()
                ts = parse_time(row.get("decided_at") or "")
                if not rid:
                    continue
                if dec not in DECISIONS or ts is None:
                    print(f"  skipping bad row {path}:{n}: {row}")
                    continue
                cur = best.get(rid)
                if cur is None or ts >= cur["ts"]:  # later decided_at wins; ties go to the later file
                    best[rid] = {"ts": ts, "decision": dec, "link_judged": row.get("link_judged") or "",
                                 "note": row.get("note") or "", "decided_at": row["decided_at"].strip()}
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="*", default=["impl_decisions_*.csv"])
    ap.add_argument("--xlsx", default=str(HERE.parent / "impl_review.xlsx"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    src = Path(a.xlsx).resolve()
    out = Path(a.out).resolve() if a.out else src.with_name("impl_review_rated.xlsx")
    if out == src:
        sys.exit("Refusing to overwrite the input workbook.")
    paths = sorted({p for pat in a.csvs for p in glob.glob(os.path.expanduser(pat))},
                   key=lambda p: (os.path.getmtime(p), p))
    if not paths:
        sys.exit(f"No CSV files match {a.csvs}")
    print(f"Reading {len(paths)} CSV file(s):")
    for p in paths:
        print("  " + p)
    best = read_decisions(paths)

    wb = openpyxl.load_workbook(src)
    ws = wb["review"]
    header = [c.value for c in ws[1]]
    rid_col = header.index("record_id") + 1
    cols = {}
    for name in NEW_COLS:
        if name in header:
            cols[name] = header.index(name) + 1
        else:
            header.append(name)
            cols[name] = len(header)
            ws.cell(row=1, column=cols[name], value=name)

    sheet_ids, counts = set(), Counter()
    for r in range(2, ws.max_row + 1):
        rid = ws.cell(row=r, column=rid_col).value
        if rid is None or str(rid).strip() == "":
            continue
        rid = str(rid).strip()
        sheet_ids.add(rid)
        d = best.get(rid)
        vals = (d["decision"], d["link_judged"], d["note"], d["decided_at"]) if d else (None,) * 4
        for name, v in zip(NEW_COLS, vals):
            ws.cell(row=r, column=cols[name], value=v)
        counts[d["decision"] if d else "unrated"] += 1

    tmp = out.with_name(out.name + ".tmp")
    wb.save(tmp)
    os.replace(tmp, out)

    print(f"\nWrote {out}")
    for k in (*DECISIONS, "unrated"):
        print(f"  {k:8} {counts[k]}")
    print(f"  total    {len(sheet_ids)}")
    unknown = sorted(set(best) - sheet_ids)
    print(f"record_ids in CSVs but not in sheet: {', '.join(unknown) if unknown else 'none'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Is merged_corpus.csv structurally sound, or are fields shifted?

    python3 diagnose_corpus.py merged_corpus.csv

Reports the field-count distribution, checks whether each column holds the kind
of value its name implies, and shows raw rows that are misaligned.
"""

import csv, re, sys
from collections import Counter

csv.field_size_limit(10_000_000)

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")
YEARISH = re.compile(r"^(19|20)\d{2}")
INTISH = re.compile(r"^\d{1,3}$")
DOIISH = re.compile(r"^(10\.|https?://doi)")
ARXIVISH = re.compile(r"^\d{4}\.\d{4,5}")


def main(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        sys.exit("empty file")

    header = rows[0]
    body = rows[1:]
    n = len(header)
    print(f"header: {n} columns")
    print(f"        {header}\n")

    counts = Counter(len(r) for r in body)
    good = counts.get(n, 0)
    print(f"rows: {len(body)} total, {good} with exactly {n} fields "
          f"({100*good/len(body):.1f}%)")
    for k in sorted(counts):
        flag = "  <-- correct" if k == n else ""
        print(f"      {counts[k]:>6} rows with {k} fields{flag}")

    bad = [r for r in body if len(r) != n]
    if bad:
        print(f"\n{len(bad)} misaligned rows. First two, field by field:")
        for r in bad[:2]:
            print(f"\n  ({len(r)} fields)")
            for i, v in enumerate(r[:n + 6]):
                name = header[i] if i < n else f"EXTRA[{i}]"
                print(f"    {i:>2} {name:<16} {v[:70]!r}")

    idx = {h.lower().strip(): i for i, h in enumerate(header)}

    def check(col, pattern, label):
        i = idx.get(col)
        if i is None:
            return
        vals = [r[i] for r in body if len(r) > i and r[i].strip()]
        if not vals:
            print(f"  {col:<14} entirely empty")
            return
        hits = sum(1 for v in vals if pattern.match(v.strip()))
        verdict = "ok" if hits / len(vals) > 0.9 else "SUSPECT"
        print(f"  {col:<14} {hits}/{len(vals)} look like {label:<12} {verdict}")

    print("\ncolumn content sanity:")
    check("merge_date", DATE, "a date")
    check("published", YEARISH, "a year")
    check("n_sources", INTISH, "an integer")
    check("doi", DOIISH, "a DOI")
    check("arxiv_id", ARXIVISH, "an arXiv id")

    ai = idx.get("abstract")
    if ai is not None:
        vals = [r[ai].strip() for r in body if len(r) > ai and r[ai].strip()]
        dateish = sum(1 for v in vals if DATE.match(v))
        longish = sum(1 for v in vals if len(v) >= 100)
        print(f"  {'abstract':<14} {len(vals)} non-empty, {longish} over 100 chars, "
              f"{dateish} are DATES  {'SUSPECT' if dateish else 'ok'}")

    print()
    if bad or (ai is not None and any(DATE.match(r[ai].strip())
                                      for r in body if len(r) > ai)):
        print("VERDICT: fields are shifted. The file was written without quoting.")
        print("Regenerate it from the three source files rather than repairing it:")
        print("  df.to_csv('merged_corpus.csv', index=False,")
        print("            quoting=csv.QUOTE_ALL, lineterminator='\\n')")
        print("Then rerun this script. Expect 100% correct field counts.")
    else:
        print("VERDICT: structurally sound. Low abstract coverage is real,")
        print("so backfill from OpenAlex or Crossref by DOI.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "merged_corpus.csv")

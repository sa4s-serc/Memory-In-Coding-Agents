#!/usr/bin/env python3
"""Restrict an OpenAlex harvest to the record types Scopus counts as
article / conference paper / preprint, for cross-source comparability.
Dropped types (software, dataset, dissertation, peer-review, ...) are not
primary studies and are reported as an exclusion count."""
import csv, sys, collections
DROP = {"peer-review", "dataset", "software", "supplementary-materials",
        "erratum", "editorial", "conference-abstract", "standard"}
src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding="utf-8")))
kept = [r for r in rows if (r.get("type") or "").lower() not in DROP]
dropped = collections.Counter((r.get("type") or "?") for r in rows
                              if (r.get("type") or "").lower() in DROP)
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(kept)
print(f"in {len(rows)} -> kept {len(kept)} -> {out}")
print("dropped:", dict(dropped.most_common()))

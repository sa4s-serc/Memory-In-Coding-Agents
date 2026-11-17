#!/usr/bin/env python3
"""
Merge and deduplicate the retrieval arms into a single screening corpus.

Dedup cascade, in order of reliability:
    1. DOI (normalised)
    2. arXiv ID (version stripped)
    3. normalised title (lowercase, alphanumeric only)
    4. fuzzy title match above threshold

Reports per-source unique yield and pairwise overlap. Marginal yield per source
is a reportable figure: it is the evidence for whether adding a source was
worth it, in the sense of Mourao et al. (IST 2020).

    python dedup_corpus.py \
        --scopus scopus_docs.csv --arxiv arxiv_corpus2.csv \
        --openalex openalex_corpus2.csv --out merged_corpus.csv
"""

import argparse
import csv
import datetime
import difflib
import os
import re
import sys

try:
    from rapidfuzz import fuzz
    def ratio(a, b):
        return fuzz.ratio(a, b)
except ImportError:
    def ratio(a, b):
        return difflib.SequenceMatcher(None, a, b).ratio() * 100


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def norm_doi(d):
    d = (d or "").strip().lower()
    d = d.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
    return d


def norm_arxiv(a):
    a = (a or "").strip()
    a = a.rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", a)


def sniff(path):
    """Read a CSV and map its columns onto a common schema."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []
    cols = {c.lower().strip(): c for c in rows[0]}

    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None

    ct = pick("title", "document title", "paper title")
    ca = pick("abstract", "summary")
    cd = pick("doi")
    cx = pick("arxiv_id", "arxiv id", "eid")
    cy = pick("published", "year", "publication_date", "publication date")
    cv = pick("venue", "source title", "journal")
    cau = pick("authors", "author names")

    out = []
    for r in rows:
        out.append({
            "title": (r.get(ct) or "").strip() if ct else "",
            "abstract": (r.get(ca) or "").strip() if ca else "",
            "doi": norm_doi(r.get(cd)) if cd else "",
            "arxiv_id": norm_arxiv(r.get(cx)) if cx else "",
            "published": (r.get(cy) or "").strip() if cy else "",
            "venue": (r.get(cv) or "").strip() if cv else "",
            "authors": (r.get(cau) or "").strip() if cau else "",
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scopus")
    ap.add_argument("--arxiv")
    ap.add_argument("--openalex")
    ap.add_argument("--out", default="merged_corpus.csv")
    ap.add_argument("--fuzzy", type=float, default=92.0)
    args = ap.parse_args()

    sources = [(n, p) for n, p in
               (("scopus", args.scopus), ("arxiv", args.arxiv),
                ("openalex", args.openalex)) if p]
    if not sources:
        sys.exit("give at least one of --scopus --arxiv --openalex")

    merged = []            # canonical records
    by_doi, by_arxiv, by_title = {}, {}, {}
    per_source = {}

    for name, path in sources:
        if not os.path.exists(path):
            print(f"skip {name}: {path} not found")
            continue
        recs = sniff(path)
        new = dup = 0
        for r in recs:
            hit = None
            if r["doi"] and r["doi"] in by_doi:
                hit = by_doi[r["doi"]]
            elif r["arxiv_id"] and r["arxiv_id"] in by_arxiv:
                hit = by_arxiv[r["arxiv_id"]]
            else:
                nt = norm_title(r["title"])
                if nt and nt in by_title:
                    hit = by_title[nt]
                elif nt:
                    for cand_nt, cand in by_title.items():
                        if abs(len(cand_nt) - len(nt)) > 12:
                            continue
                        if ratio(cand_nt, nt) >= args.fuzzy:
                            hit = cand
                            break
            if hit is not None:
                hit["sources"].add(name)
                dup += 1
                for k in ("doi", "arxiv_id", "abstract", "venue", "authors"):
                    if not hit[k] and r[k]:
                        hit[k] = r[k]
                if r["doi"]:
                    by_doi.setdefault(r["doi"], hit)
                if r["arxiv_id"]:
                    by_arxiv.setdefault(r["arxiv_id"], hit)
                continue
            rec = dict(r, sources={name})
            merged.append(rec)
            new += 1
            if rec["doi"]:
                by_doi[rec["doi"]] = rec
            if rec["arxiv_id"]:
                by_arxiv[rec["arxiv_id"]] = rec
            nt = norm_title(rec["title"])
            if nt:
                by_title[nt] = rec
        per_source[name] = {"records": len(recs), "new": new, "dup": dup}
        print(f"{name:<10} {len(recs):>5} records  {new:>5} new  {dup:>5} already seen")

    date = datetime.date.today().isoformat()
    cols = ["id", "title", "authors", "published", "venue", "doi", "arxiv_id",
            "n_sources", "sources", "merge_date", "stage1_relevant",
            "stage2_bucket", "stage3_tier", "notes", "abstract"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, r in enumerate(merged, 1):
            s = sorted(r["sources"])
            w.writerow({
                "id": f"R{i:05d}", "title": r["title"], "authors": r["authors"],
                "published": r["published"], "venue": r["venue"],
                "doi": r["doi"], "arxiv_id": r["arxiv_id"],
                "n_sources": len(s), "sources": ";".join(s),
                "merge_date": date, "stage1_relevant": "", "stage2_bucket": "",
                "stage3_tier": "", "notes": "", "abstract": r["abstract"],
            })

    print(f"\nmerged unique records : {len(merged)}")
    print(f"written               : {args.out}\n")

    print("unique contribution per source (records found by that source alone)")
    for name, _ in sources:
        only = sum(1 for r in merged if r["sources"] == {name})
        tot = sum(1 for r in merged if name in r["sources"])
        if tot:
            print(f"  {name:<10} in {tot:>5}   unique to it {only:>5} "
                  f"({only/tot:.1%} of its own yield)")

    names = [n for n, _ in sources]
    if len(names) > 1:
        print("\npairwise overlap")
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                both = sum(1 for r in merged
                           if a in r["sources"] and b in r["sources"])
                print(f"  {a} & {b}: {both}")

    multi = sum(1 for r in merged if len(r["sources"]) > 1)
    print(f"\nfound by more than one source: {multi} "
          f"({multi/len(merged):.1%})" if merged else "")


if __name__ == "__main__":
    main()

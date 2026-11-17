#!/usr/bin/env python3
"""
arXiv harvest of the preprint arm, patched blocks, frozen 2 Aug 2026.

Scopus remains the primary instrument and the source of reported counts.
arXiv is the retrieval mechanism for the preprint arm, because the Scopus
Preprints collection (Beta) offers no bulk export.

Strategy: the arXiv API is queried with the C and M blocks (the two most
restrictive), one query per C term to keep each request short and avoid
timeouts. All four blocks are then applied locally by regex, so the final
membership test is identical to the frozen string rather than dependent on
arXiv query semantics. Wildcards are hand-expanded for the API because arXiv
does not handle truncation reliably; the local regexes use prefix matching.

    python arxiv_harvest.py --out arxiv_corpus2.csv
    python arxiv_harvest.py --out arxiv_corpus1.csv --no-code-block

Output columns include empty screening fields for the three-stage pipeline:
stage1_relevant, stage2_bucket, stage3_tier.
"""

import argparse
import csv
import datetime
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ARXIV = "http://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"

# --- Local membership test: the frozen blocks as regex (prefix matching) ----

BLOCKS = {
    "L": [r"large language model", r"\bLLMs?\b", r"language model",
          r"foundation model", r"coding agent", r"code agent",
          r"software engineering agent", r"SWE[ -]agent"],
    "G": [r"\bagent", r"agentic", r"multi-?agent"],
    "M": [r"\bmemory\b", r"\bmemories\b", r"\bexperience", r"reflection",
          r"trajector", r"continual learning", r"lifelong learning",
          r"self-?improv", r"self-?evolv", r"knowledge accumulation",
          r"skill librar", r"case-based reasoning", r"context management",
          r"context compression", r"context pruning", r"context folding"],
    "C": [r"software engineering", r"software development", r"code generation",
          r"code completion", r"program repair", r"issue resolution",
          r"bug fix", r"repositor", r"codebase", r"SWE-?bench", r"SWE-?agent",
          r"coding agent", r"software agent", r"\bSWE\b"],
}

# --- API query terms: wildcards hand-expanded ------------------------------

C_QUERY_TERMS = [
    '"software engineering"', '"software development"', '"code generation"',
    '"code completion"', '"program repair"', '"issue resolution"',
    '"bug fix"', '"bug fixes"', '"bug fixing"', '"repository"',
    '"repositories"', '"codebase"', '"SWE-bench"', '"SWE-agent"',
    '"coding agent"', '"coding agents"', '"software agent"',
    '"software agents"', '"SWE"',
]

M_QUERY_TERMS = [
    '"memory"', '"memories"', '"experience"', '"experiences"', '"reflection"',
    '"trajectory"', '"trajectories"', '"continual learning"',
    '"lifelong learning"', '"self-improving"', '"self-improvement"',
    '"self-evolving"', '"self-evolution"', '"knowledge accumulation"',
    '"skill library"', '"skill libraries"', '"case-based reasoning"',
    '"context management"', '"context compression"', '"context pruning"',
    '"context folding"',
]

MIN_YEAR = 0  # PUBYEAR > 2022


def field_or(terms):
    """OR a term list across title and abstract."""
    parts = []
    for t in terms:
        parts.append(f"ti:{t}")
        parts.append(f"abs:{t}")
    return "(" + " OR ".join(parts) + ")"


def query_arxiv(search, start, page):
    q = urllib.parse.urlencode({
        "search_query": search, "start": start, "max_results": page,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f"{ARXIV}?{q}", timeout=90) as r:
                return ET.fromstring(r.read())
        except Exception as e:
            if attempt == 3:
                print(f"    failed after retries: {e}")
                return None
            time.sleep(6 * (attempt + 1))
    return None


def parse(root):
    out = []
    for e in root.findall(f"{ATOM}entry"):
        aid = re.sub(r"v\d+$", "",
                     e.findtext(f"{ATOM}id", "").rsplit("/", 1)[-1])
        cats = [c.attrib.get("term", "") for c in e.findall(f"{ATOM}category")]
        out.append({
            "arxiv_id": aid,
            "title": " ".join((e.findtext(f"{ATOM}title") or "").split()),
            "abstract": " ".join((e.findtext(f"{ATOM}summary") or "").split()),
            "published": (e.findtext(f"{ATOM}published") or "")[:10],
            "updated": (e.findtext(f"{ATOM}updated") or "")[:10],
            "categories": ";".join(sorted(set(c for c in cats if c))),
            "authors": "; ".join(
                a.findtext(f"{ATOM}name") or ""
                for a in e.findall(f"{ATOM}author")[:5]),
        })
    return out


def passes(rec, blocks):
    text = f"{rec['title']} {rec['abstract']}"
    return all(any(re.search(t, text, re.I) for t in BLOCKS[b]) for b in blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="arxiv_corpus2.csv")
    ap.add_argument("--no-code-block", action="store_true",
                    help="Corpus 1: drop block C from the local test")
    ap.add_argument("--page", type=int, default=100)
    ap.add_argument("--max-per-term", type=int, default=2000)
    args = ap.parse_args()

    blocks = ("L", "M") if args.no_code_block else ("L", "M", "C")
    m_clause = field_or(M_QUERY_TERMS)
    seen, raw_total = {}, 0

    for i, cterm in enumerate(C_QUERY_TERMS, 1):
        search = f"({field_or([cterm])}) AND {m_clause}"
        print(f"[{i}/{len(C_QUERY_TERMS)}] {cterm}", flush=True)
        start = 0
        while start < args.max_per_term:
            root = query_arxiv(search, start, args.page)
            if root is None:
                break
            batch = parse(root)
            if not batch:
                break
            raw_total += len(batch)
            for rec in batch:
                if rec["arxiv_id"] in seen:
                    continue
                if rec["published"] and int(rec["published"][:4]) < MIN_YEAR:
                    continue
                seen[rec["arxiv_id"]] = rec
            if len(batch) < args.page:
                break
            start += args.page
            time.sleep(3.1)
        print(f"    running unique: {len(seen)}", flush=True)
        time.sleep(3.1)

    kept = [r for r in seen.values() if passes(r, blocks)]
    kept.sort(key=lambda r: r["published"], reverse=True)

    date = datetime.date.today().isoformat()
    cols = ["arxiv_id", "title", "authors", "published", "updated",
            "categories", "harvest_date", "stage1_relevant", "stage2_bucket",
            "stage3_tier", "notes", "abstract"]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in kept:
            w.writerow({**{k: r.get(k, "") for k in
                           ("arxiv_id", "title", "authors", "published",
                            "updated", "categories", "abstract")},
                        "harvest_date": date, "stage1_relevant": "",
                        "stage2_bucket": "", "stage3_tier": "", "notes": ""})

    print(f"\nraw records seen      : {raw_total}")
    print(f"unique after dedup    : {len(seen)}")
    print(f"pass {'+'.join(blocks):<15}: {len(kept)}")
    print(f"written               : {args.out}")


if __name__ == "__main__":
    main()

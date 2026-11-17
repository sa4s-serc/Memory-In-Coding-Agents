#!/usr/bin/env python3
"""
OpenAlex harvest, frozen blocks, second retrieval source for the preprint arm.

OpenAlex indexes arXiv plus other preprint servers (TechRxiv, Preprints.org,
SSRN, Research Square), which is closer to the coverage the Scopus Preprints
collection claims than arXiv alone.

Same strategy as the arXiv harvester: query the API with the C and M blocks to
retrieve a superset, then apply all four frozen blocks locally by regex so the
membership test is identical across sources.

    python openalex_harvest.py --out openalex_corpus2.csv --mailto you@iiit.ac.in

The mailto goes into the polite pool and is materially faster. Abstracts arrive
as inverted indexes and are reconstructed here.
"""

import argparse
import csv
import datetime
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.openalex.org/works"

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

C_TERMS = [
    "software engineering", "software development", "code generation",
    "code completion", "program repair", "issue resolution", "bug fixing",
    "repository", "codebase", "SWE-bench", "SWE-agent", "coding agent",
    "software agent", "SWE",
]

M_TERMS = [
    "memory", "experience", "reflection", "trajectory", "continual learning",
    "lifelong learning", "self-improvement", "self-evolving",
    "knowledge accumulation", "skill library", "case-based reasoning",
    "context management", "context compression", "context pruning",
    "context folding",
]

L_TERMS = [
    "large language model", "large language models", "LLM", "LLMs",
    "language model", "language models", "foundation model",
    "coding agent", "coding agents", "code agent", "code agents",
    "software engineering agent", "software engineering agents",
    "SWE agent", "SWE agents",
]

FROM_DATE = "2023-01-01"


def deinvert(idx):
    """Reconstruct plain text from an OpenAlex abstract_inverted_index."""
    if not idx:
        return ""
    pos = []
    for word, locs in idx.items():
        for l in locs:
            pos.append((l, word))
    pos.sort()
    return " ".join(w for _, w in pos)


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(5 * (i + 1))
                continue
            print(f"    HTTP {e.code}")
            return None
        except Exception as e:
            if i == tries - 1:
                print(f"    {e}")
                return None
            time.sleep(4 * (i + 1))
    return None


def harvest_term(cterm, mailto, per_page=200, max_pages=40):
    m_clause = " OR ".join(f'"{t}"' for t in M_TERMS)
    l_clause = " OR ".join(f'"{t}"' for t in L_TERMS)
    search = f'"{cterm}" AND ({m_clause}) AND ({l_clause})'
    out, cursor = [], "*"
    total = None
    for page in range(max_pages):
        params = {
            "filter": f"title_and_abstract.search:{search},"
                      f"from_publication_date:{FROM_DATE}",
            "per-page": per_page,
            "cursor": cursor,
            "select": "id,doi,title,publication_date,type,"
                      "abstract_inverted_index,primary_location,authorships",
        }
        if mailto:
            params["mailto"] = mailto
        data = get(f"{API}?{urllib.parse.urlencode(params)}")
        if not data:
            break
        meta = data.get("meta") or {}
        if total is None:
            total = meta.get("count")
            print(f"    API count: {total}", flush=True)
        results = data.get("results", [])
        out.extend(results)
        print(f"    page {page+1}: +{len(results)}  (have {len(out)})", flush=True)
        cursor = meta.get("next_cursor")
        if not cursor or len(results) < per_page:
            break
        time.sleep(0.3)
    return out


def normalise(w):
    loc = w.get("primary_location") or {}
    src = (loc.get("source") or {}).get("display_name") or ""
    landing = loc.get("landing_page_url") or ""
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    arxiv = ""
    m = re.search(r"arxiv\.org/abs/([\d.]+)", landing, re.I)
    if m:
        arxiv = m.group(1)
    elif "arxiv" in doi.lower():
        m2 = re.search(r"([\d]{4}\.[\d]{4,5})", doi)
        arxiv = m2.group(1) if m2 else ""
    return {
        "openalex_id": (w.get("id") or "").rsplit("/", 1)[-1],
        "doi": doi,
        "arxiv_id": arxiv,
        "title": " ".join((w.get("title") or "").split()),
        "abstract": deinvert(w.get("abstract_inverted_index")),
        "published": w.get("publication_date") or "",
        "type": w.get("type") or "",
        "venue": src,
        "authors": "; ".join(
            (a.get("author") or {}).get("display_name") or ""
            for a in (w.get("authorships") or [])[:5]),
    }


def passes(rec, blocks=("L", "M", "C")):
    text = f"{rec['title']} {rec['abstract']}"
    return all(any(re.search(t, text, re.I) for t in BLOCKS[b]) for b in blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="openalex_corpus2.csv")
    ap.add_argument("--mailto", help="email for the OpenAlex polite pool")
    ap.add_argument("--no-code-block", action="store_true")
    args = ap.parse_args()

    blocks = ("L", "M") if args.no_code_block else ("L", "M", "C")
    seen, raw = {}, 0

    for i, cterm in enumerate(C_TERMS, 1):
        print(f"[{i}/{len(C_TERMS)}] {cterm}", flush=True)
        works = harvest_term(cterm, args.mailto)
        raw += len(works)
        for w in works:
            rec = normalise(w)
            key = rec["openalex_id"]
            if key and key not in seen:
                seen[key] = rec
        print(f"    running unique: {len(seen)}", flush=True)

    kept = [r for r in seen.values() if passes(r, blocks)]
    kept.sort(key=lambda r: r["published"], reverse=True)

    date = datetime.date.today().isoformat()
    cols = ["openalex_id", "doi", "arxiv_id", "title", "authors", "published",
            "type", "venue", "harvest_date", "source", "stage1_relevant",
            "stage2_bucket", "stage3_tier", "notes", "abstract"]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in kept:
            w.writerow({**r, "harvest_date": date, "source": "openalex",
                        "stage1_relevant": "", "stage2_bucket": "",
                        "stage3_tier": "", "notes": ""})

    types = {}
    for r in kept:
        types[r["type"]] = types.get(r["type"], 0) + 1
    print(f"\nraw records          : {raw}")
    print(f"unique               : {len(seen)}")
    print(f"pass {'+'.join(blocks):<16}: {len(kept)}")
    print("by type              :", dict(sorted(types.items(),
                                                key=lambda kv: -kv[1])))
    print(f"written              : {args.out}")


if __name__ == "__main__":
    main()

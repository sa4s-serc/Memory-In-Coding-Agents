# /// script
# dependencies = ["openpyxl", "pypdf"]
# ///
"""Validate classification results and join them to the rated sheet on record_id.

Usage:  uv run classification/join_results.py [--results DIR] [--out FILE]
Writes classification_joined.xlsx (one row per manifest paper, in manifest order)
and exits non-zero unless every paper is either valid or recorded in errors.txt.
"""
import argparse
import csv
import json
import logging
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import openpyxl
from pypdf import PdfReader

logging.disable(logging.CRITICAL)
HERE = Path(__file__).resolve().parent
SCOPES = {"WITHIN", "CROSS", "EXTERNAL", "NOT_APPLICABLE"}
NA = {"NO_MECHANISM", "PARAMETRIC", "CONTEXT_FILES"}
SOURCES = {"within", "cross", "external"}
ORIGINS = {"own_trajectories", "others_tasks", "both"}
ROLES = {"CORE", "COMPONENT"}
ACTIVITIES = {"REQUIREMENTS_ENGINEERING", "SOFTWARE_DESIGN", "SOFTWARE_DEVELOPMENT",
              "QUALITY_ASSURANCE", "SOFTWARE_MAINTENANCE", "SOFTWARE_MANAGEMENT"}
FIELDS = ["mechanism", "scope", "na_reason", "sources", "cross_origin", "role", "activity", "target",
          "evidence_scope", "evidence_role", "read_full_text"]
HIDE_FIELDS = {"na_reason", "read_full_text"}  # checked, but not written to the sheet
HIDE_RATED = {"evidence", "repo_check"}        # rated-sheet columns not carried over


def squash(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", s or "").lower())


def pdf_text(path):
    return squash(" ".join(p.extract_text() or "" for p in PdfReader(path).pages))


def check(r, row, text):
    """Return a list of problems with one result."""
    bad = []
    missing = [f for f in ["record_id", "pdf_sha256", *FIELDS] if f not in r]
    if missing:
        return [f"missing fields: {', '.join(missing)}"]
    if r["record_id"] != row["record_id"]:
        bad.append(f"record_id is {r['record_id']}")
    if r["pdf_sha256"] != row["pdf_sha256"]:
        bad.append("pdf_sha256 does not match manifest")
    if r["scope"] not in SCOPES:
        bad.append(f"bad scope {r['scope']}")
    if (r["scope"] == "NOT_APPLICABLE") != (r["na_reason"] in NA):
        bad.append("scope and na_reason disagree")
    sources = r["sources"] if isinstance(r["sources"], list) else []
    if not set(sources) <= SOURCES:
        bad.append(f"bad sources {r['sources']}")
    if r["scope"] in ("WITHIN", "CROSS", "EXTERNAL"):
        want = "CROSS" if "cross" in sources else "EXTERNAL" if "external" in sources else "WITHIN"
        if want != r["scope"]:
            bad.append(f"sources imply {want}, scope is {r['scope']}")
    if ("cross" in sources) != (r["cross_origin"] in ORIGINS):
        bad.append("cross_origin and sources disagree")
    no_mech = r["na_reason"] == "NO_MECHANISM"
    if not no_mech and r["role"] not in ROLES:
        bad.append(f"bad role {r['role']}")
    if not no_mech and r["activity"] not in ACTIVITIES:
        bad.append(f"bad activity {r['activity']}")
    if r["read_full_text"] is not True:
        bad.append("read_full_text is not true")
    for name in ("evidence_scope", "evidence_role"):
        quote = r[name] or ""
        if len(quote.split()) >= 100:
            bad.append(f"{name} is 100 words or more")
        if quote and squash(quote) not in text:  # proves the quote came from this PDF
            bad.append(f"{name} not found in the PDF")
        if not quote and not no_mech:
            bad.append(f"{name} is empty")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(HERE / "results"))
    ap.add_argument("--errors", default=str(HERE / "errors.txt"))
    ap.add_argument("--out", default=str(HERE / "classification_joined.xlsx"))
    a = ap.parse_args()

    manifest = list(csv.DictReader(open(HERE / "manifest.csv", encoding="utf-8-sig", newline="")))
    ids = {m["record_id"] for m in manifest}
    assert len(ids) == len(manifest), "duplicate record_id in manifest"
    errors = {}
    for line in Path(a.errors).read_text(encoding="utf-8").splitlines():
        if line.strip():
            errors[line.split("|")[0].strip()] = line.strip()

    results_dir = Path(a.results)
    strays = sorted(p.name for p in results_dir.glob("*.json") if p.stem not in ids)

    wb = openpyxl.load_workbook(HERE.parent / "rated_implementations_final.xlsx", read_only=True, data_only=True)
    rows = wb["review"].iter_rows(values_only=True)
    header = list(next(rows))
    rated = {r[0]: r for r in rows if r[0]}
    assert set(rated) == ids, "manifest and rated_implementations_final.xlsx list different papers"

    out = openpyxl.Workbook()
    ws = out.active
    ws.title = "classified"
    # Columns left out of the sheet (still computed and checked): status and problems drive the
    # printed counts and exit code; na_reason and read_full_text are validated but not shown;
    # evidence and repo_check come from the rated sheet and are not needed here.
    SHOW = [f for f in FIELDS if f not in HIDE_FIELDS]
    keep = [i for i, h in enumerate(header[1:], start=1) if h not in HIDE_RATED]
    ws.append(["record_id", "pdf_sha256", *SHOW, *[header[i] for i in keep]])
    status = Counter()
    for m in manifest:
        rid = m["record_id"]
        path = results_dir / f"{rid}.json"
        r, problems = {}, []
        if path.exists():
            try:
                r = json.loads(path.read_text(encoding="utf-8"))
                problems = check(r, m, pdf_text(HERE / m["pdf"]) if m["pdf"] else "")
            except (ValueError, OSError) as e:
                r, problems = {}, [f"unreadable JSON: {e}"]
            state = "invalid" if problems else "classified"
            if rid in errors:
                state, problems = "invalid", [*problems, "also listed in errors.txt"]
        elif rid in errors:
            state, problems = "error", [errors[rid]]
        else:
            state = "missing"
        status[state] += 1
        vals = [", ".join(r[f]) if f == "sources" and isinstance(r.get(f), list) else r.get(f) for f in SHOW]
        ws.append([rid, m["pdf_sha256"], *vals, *[rated[rid][i] for i in keep]])
    tmp = Path(a.out + ".tmp.xlsx")
    out.save(tmp)
    tmp.replace(a.out)

    print(f"Wrote {a.out}")
    for k in ("classified", "error", "invalid", "missing"):
        print(f"  {k:11}{status[k]}")
    if strays:
        print(f"Result files with no manifest row: {', '.join(strays)}")
    sys.exit(1 if status["invalid"] or status["missing"] or strays else 0)


if __name__ == "__main__":
    main()

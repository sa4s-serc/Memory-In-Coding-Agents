#!/usr/bin/env python3
"""Draw the Stage 1 human-validation sample and write one blind labelling sheet per rater.

  python make_stage1_sample.py
  python make_stage1_sample.py --corpus corpus.csv \
      --screened screened_qwen3.5_397b_r1.jsonl --per-band 30 --seed 20261029

Bands (by the model's include score): high >= 0.70, mid 0.50-0.69, low < 0.50.
The same records go to both raters, in different random orders. Neither sheet shows
the model's score or bucket. The key linking sample ids to scores is written to
stage1_sample_key.xlsx: do not open it until both raters have finished.

Outputs (Excel only, so commas, quotes and line breaks in abstracts cannot break anything):
  stage1_labels_PSK.xlsx, stage1_labels_Aviral.xlsx, stage1_sample_key.xlsx
"""
import argparse, csv, json, random, sys
from collections import Counter
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font
from openpyxl.worksheet.datavalidation import DataValidation

csv.field_size_limit(sys.maxsize)
BANDS = [("high", 0.70, 1.01), ("mid", 0.50, 0.70), ("low", 0.0, 0.50)]
CRITERIA = (
    "INCLUDE if ALL hold. IC1: proposes, evaluates, studies or benchmarks a memory or "
    "information-handling mechanism for an LLM-based agent (context compression, pruning, "
    "summarisation, folding, scratchpads, retrieval over prior work, experience stores, skill "
    "libraries, self-evolving behaviour, cross-task knowledge reuse). IC2: applied to or "
    "evaluated on code generation or software engineering tasks. Surveys and benchmarks that "
    "meet IC1 and IC2 are INCLUDE. EXCLUDE if IC1 or IC2 fails, or EC1: evaluation is purely "
    "conversational, QA, or general-domain with no code or SE component.")


def clean(s):
    return ILLEGAL_CHARACTERS_RE.sub("", s or "").strip()


def load_corpus(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit(f"{path}: no rows")
    cols = {c.lower().strip(): c for c in rows[0]}
    idc = next((cols[k] for k in ("id", "record_id", "uid", "key") if k in cols), None)
    tic, abc = cols.get("title"), cols.get("abstract")
    if not (idc and tic and abc):
        sys.exit(f"{path}: need id, title, abstract columns; found {list(rows[0])}")
    ids = [r[idc].strip() for r in rows]
    dup = [k for k, n in Counter(ids).items() if n > 1]
    if dup:
        sys.exit(f"{path}: duplicate ids, the file may be malformed: {dup[:5]}")
    bad = [i for i in ids if not i.startswith("R")]
    if bad:
        sys.exit(f"{path}: unexpected id values (a row may have split): {bad[:5]}")
    return {r[idc].strip(): (clean(r[tic]), clean(r[abc])) for r in rows}


def load_scores(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if ln.strip():
                o = json.loads(ln)
                out[o["id"]] = float(o["include"])
    return out


def band_of(p):
    return next(b for b, lo, hi in BANDS if lo <= p < hi)


def write_sheet(path, rows, rater):
    wb = Workbook()
    ws = wb.active
    ws.title = "labels"
    head = ["sample_id", "title", "abstract", "decision", "note"]
    ws.append(head)
    for r in rows:
        ws.append([r["sample_id"], r["title"], r["abstract"], None, None])
    for c in ws[1]:
        c.font = Font(bold=True)
    for col, w in zip("ABCDE", (11, 45, 110, 12, 30)):
        ws.column_dimensions[col].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
        row[0].number_format = "@"
    ws.freeze_panes = "B2"
    dv = DataValidation(type="list", formula1='"INCLUDE,EXCLUDE"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Invalid",
                        error="Choose INCLUDE or EXCLUDE")
    ws.add_data_validation(dv)
    dv.add(f"D2:D{len(rows) + 1}")
    info = wb.create_sheet("instructions")
    for line in [f"Rater: {rater}", "", "Label each record from its title and abstract only.",
                 "Fill column D with INCLUDE or EXCLUDE. Use column E for anything uncertain.",
                 "Do not look at the other rater's sheet or the key file until both are done.",
                 "", "Criteria:", CRITERIA]:
        info.append([line])
    info.column_dimensions["A"].width = 120
    info["A8"].alignment = Alignment(wrap_text=True)
    wb.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus.csv")
    ap.add_argument("--screened", default="screened_qwen3.5_397b_r1.jsonl")
    ap.add_argument("--per-band", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--raters", default="PSK,Aviral")
    a = ap.parse_args()

    corpus = load_corpus(a.corpus)
    scores = load_scores(a.screened)
    missing = [i for i in scores if i not in corpus]
    if missing:
        sys.exit(f"{len(missing)} scored ids not in corpus, e.g. {missing[:5]}")
    print(f"corpus rows: {len(corpus)}   scored: {len(scores)}")

    rng = random.Random(a.seed)
    pool = {b: sorted(i for i, p in scores.items() if band_of(p) == b) for b, _, _ in BANDS}
    picked = []
    for b, _, _ in BANDS:
        if len(pool[b]) < a.per_band:
            sys.exit(f"band {b} has only {len(pool[b])} records")
        for rid in rng.sample(pool[b], a.per_band):
            picked.append({"record_id": rid, "band": b, "band_size": len(pool[b]),
                           "score": scores[rid]})
        print(f"band {b:<4}: population {len(pool[b]):>5}, sampled {a.per_band}")

    rng.shuffle(picked)
    for n, r in enumerate(picked, 1):
        r["sample_id"] = f"S{n:03d}"
        r["title"], r["abstract"] = corpus[r["record_id"]]

    for rater in a.raters.split(","):
        rows = picked[:]
        random.Random(f"{a.seed}-{rater}").shuffle(rows)
        write_sheet(f"stage1_labels_{rater}.xlsx", rows, rater)
        print(f"wrote stage1_labels_{rater}.xlsx ({len(rows)} records)")

    wb = Workbook()
    ws = wb.active
    ws.title = "key"
    ws.append(["sample_id", "record_id", "band", "band_size", "model_score",
               "model_decision", "seed"])
    for r in sorted(picked, key=lambda r: r["sample_id"]):
        ws.append([r["sample_id"], r["record_id"], r["band"], r["band_size"], r["score"],
                   "INCLUDE" if r["score"] >= 0.70 else "EXCLUDE", a.seed])
    wb.save("stage1_sample_key.xlsx")
    print("wrote stage1_sample_key.xlsx (not to be opened until labelling is done)")


if __name__ == "__main__":
    main()

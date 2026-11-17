# /// script
# dependencies = ["openpyxl"]
# ///
"""Draw the second-rater sample: simple random sample of 50 papers, kept in sheet order.

Reads impl_review.xlsx (never the rated file), so the output carries no first-rater ratings.
Usage:  uv run link_review/sample_aviral.py
"""
import random
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
SEED = 20261030
N = 50

src = openpyxl.load_workbook(HERE.parent / "impl_review.xlsx", read_only=True, data_only=True)["review"]
rows = src.iter_rows(values_only=True)
header = next(rows)
papers = [r for r in rows if r[0]]
picked = sorted(random.Random(SEED).sample(range(len(papers)), N))

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "review"
ws.append(header)
for i in picked:
    ws.append(papers[i])
wb.save(HERE.parent / "impl_results_Aviral.xlsx")
print(f"Sampled {N} of {len(papers)} with seed {SEED}")

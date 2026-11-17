"""Draw the kappa sample: a simple random sample of 30 of the 289 classified papers.

Writes two files next to this script:
  sample_30.csv     what AG needs (id, title, links). No classification labels.
  PSK_labelled_30.csv  the classification of the same 30 papers.
It also copies the 30 PDFs into papers, so the folder can be zipped and shared.

Usage:  python3 kappa_review/make_sample.py
"""
import csv
import json
import random
import re
import shutil
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SEED = 20261103
N = 30
ARXIV = re.compile(r"^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?$")

(HERE / "papers").mkdir(exist_ok=True)
manifest = list(csv.DictReader(open(ROOT / "manifest.csv", encoding="utf-8-sig")))
picked = sorted(random.Random(SEED).sample(range(len(manifest)), N))

with open(HERE / "sample_30.csv", "w", newline="", encoding="utf-8-sig") as f, \
     open(HERE / "PSK_labelled_30.csv", "w", newline="", encoding="utf-8-sig") as g:
    w = csv.writer(f, quoting=csv.QUOTE_ALL)
    v = csv.writer(g, quoting=csv.QUOTE_ALL)
    w.writerow(["record_id", "manifest_row", "title", "arxiv_id", "doi", "online_link", "local_pdf"])
    v.writerow(["record_id", "scope", "na_reason", "cross_origin", "role", "activity", "mechanism"])
    for i in picked:
        m = manifest[i]
        rid = m["record_id"]
        arx = m["arxiv_id"].strip() if ARXIV.match(m["arxiv_id"].strip()) else ""
        doi = m["doi"].strip()
        link = (f"https://arxiv.org/abs/{arx}" if arx else f"https://doi.org/{doi}" if doi
                else "https://scholar.google.com/scholar?q=" + quote(m["title"]))
        shutil.copyfile(ROOT / m["pdf"], HERE / "papers" / f"{rid}.pdf")
        w.writerow([rid, i + 1, m["title"], arx, doi, link, f"papers/{rid}.pdf"])
        r = json.load(open(ROOT / "results" / f"{rid}.json", encoding="utf-8"))
        v.writerow([rid, r["scope"], r["na_reason"] or "", r["cross_origin"] or "", r["role"] or "",
                    r["activity"] or "", r.get("mechanism", "")])
print(f"Sampled {N} of {len(manifest)} with seed {SEED}")

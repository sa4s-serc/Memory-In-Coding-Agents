"""Step 1. List the 151 WITHIN/CROSS papers and extract their full text, page by page,
up to the references, plus appendix pages with a limitations-type heading.

Output: results/papers.csv           record_id, scope, role, pilot (0/1)
        results/text/<record_id>.txt  pages headed "[p. N]"
        results/text_log.csv          incl. appendix_pages (pages kept after the references)
"""
import csv
import re

import pymupdf

from rq3_common import OUT, find_pdf, load_classification, pilot_ids

REFS = re.compile(r"^\s*(?:[0-9IVX]+\.?\s+)?(references|bibliography)\s*$", re.I | re.M)
HEAD, TAIL = 40_000, 80_000   # if the main body is longer than HEAD+TAIL characters: keep its start and end
# Appendix pages after the references are kept only if they carry a limitations-type heading
# (many NeurIPS/ICML-style papers put "Limitations" in the appendix). That page and the next are kept.
APX_HEAD = re.compile(
    r"^\s*(?:[A-Z]|[A-Z]?\d+(?:\.\d+)*)?\.?\s*"
    r"(?:limitations?\b.*|threats to (?:the )?validity.*|discussion\b.*|conclusions? and (?:limitations|future work).*"
    r"|future (?:work|directions)\.?|broader impacts?.*|impact statement.*)$", re.I | re.M)
CHECKLIST = re.compile(r"paper checklist|Question:\s*Does the paper", re.I)
APX_MAX = 8   # at most this many appendix pages per paper


def _heading(t):
    return any(len(m.group(0).strip()) <= 70 for m in APX_HEAD.finditer(t))


def fulltext(pdf):
    doc = pymupdf.open(pdf)
    pages, ref_page = [], None
    for i, page in enumerate(doc, 1):
        t = page.get_text("text")
        m = REFS.search(t)
        if m and i > 2:
            pages.append(f"[p. {i}]\n{t[:m.start()]}")
            ref_page = i
            break
        pages.append(f"[p. {i}]\n{t}")
    txt = "\n".join(pages)
    if len(txt) > HEAD + TAIL:
        txt = txt[:HEAD] + "\n[... middle of the paper omitted ...]\n" + txt[-TAIL:]
    keep = []
    if ref_page:
        for i in range(ref_page + 1, len(doc) + 1):          # 1-based page numbers
            t = doc[i - 1].get_text("text")
            if CHECKLIST.search(t) or not _heading(t):
                continue
            keep += [p for p in (i, i + 1) if p <= len(doc) and p not in keep]
        keep = [p for p in keep if not CHECKLIST.search(doc[p - 1].get_text("text"))][:APX_MAX]
    if keep:
        txt += "\n[... references and other appendix pages omitted ...]\n" + "\n".join(
            f"[p. {p}]\n{doc[p - 1].get_text('text')}" for p in keep)
    return txt, len(keep)


OUT.mkdir(exist_ok=True)
(OUT / "text").mkdir(exist_ok=True)
cls = load_classification()
wc = cls[cls.scope.isin(["WITHIN", "CROSS"])].sort_values("record_id").copy()
pilot = set(pilot_ids())
if pilot - set(wc.record_id):
    raise SystemExit(f"Pilot ids not WITHIN/CROSS: {sorted(pilot - set(wc.record_id))}")
wc["pilot"] = wc.record_id.isin(pilot).astype(int)
wc.to_csv(OUT / "papers.csv", index=False)

log = []
for rid in wc.record_id:
    pdf = find_pdf(rid)
    if pdf is None:
        log.append((rid, "", 0, 0, "NO_PDF"))
        continue
    t, n_apx = fulltext(pdf)
    (OUT / "text" / f"{rid}.txt").write_text(t, encoding="utf-8")
    log.append((rid, pdf.name, len(t), n_apx, "OK" if len(t) > 2000 else "SHORT"))
with open(OUT / "text_log.csv", "w", newline="") as f:
    csv.writer(f).writerows([("record_id", "pdf", "chars", "appendix_pages", "status"), *log])
st = [s for *_, s in log]
print(f"papers {len(wc)} (WITHIN {sum(wc.scope == 'WITHIN')}, CROSS {sum(wc.scope == 'CROSS')}, pilot {len(pilot)})")
print(f"text OK {st.count('OK')}, short {st.count('SHORT')}, no pdf {st.count('NO_PDF')}")
apx = [r for r, _, _, n, _ in log if n]
print(f"appendix limitation pages added for {len(apx)} papers: {apx}")

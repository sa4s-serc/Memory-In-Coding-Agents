"""Shared paths and helpers for the RQ3 extraction scripts. Edit PATHS once."""
import json
import re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
PATHS = {
    # Inputs from the classification step; only steps 1-2 need them. Adjust to where they sit in the package.
    "classification": HERE.parent.parent / "classification_joined.xlsx",
    "pdf_dir": HERE.parent.parent / "pdfs",                  # PDF names must contain the record id
    "pilot_list": HERE / "pilot_sample.txt",                 # the 30 pilot papers (excluded from the human sample)
}
MODELS = {"A": "deepseek-v4-pro:0813", "B": "glm-5.3"}       # Ollama model names
# Ollama "think" per model: None = server default (key not sent), True/False = sent explicitly.
# glm-5.3's default thinking runs away on the full-text prompt (>100k chars, no answer); off answers in ~3 s.
THINK = {"A": None, "B": False}
OUT = HERE.parent / "results"
SEED_HUMAN = 20261115
N_HUMAN = 30
# ---------------------------------------------------------------------------

RID = re.compile(r"R\d{5}")


def form():
    return json.loads((HERE / "extraction_form_v1.json").read_text(encoding="utf-8"))


def field_ids():
    return [f["id"] for f in form()["fields"]]


def slug(model):
    return re.sub(r"[^A-Za-z0-9.-]", "_", model)


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _find_col(df, values):
    best, score = None, 0.0
    for c in df.columns:
        v = df[c].dropna().astype(str).str.strip()
        if len(v):
            s = v.isin(values).mean()
            if s > score:
                best, score = c, s
    return best if score >= 0.8 else None


def load_classification():
    df = pd.read_excel(PATHS["classification"])
    rid = next((c for c in df.columns if df[c].astype(str).str.fullmatch(r"R\d{5}").mean() > 0.9), None)
    scope = _find_col(df, {"WITHIN", "CROSS", "EXTERNAL", "NOT_APPLICABLE"})
    role = _find_col(df, {"CORE", "COMPONENT"})
    if rid is None or scope is None:
        raise SystemExit(f"Record id / scope columns not found. Columns: {list(df.columns)}")
    out = pd.DataFrame({"record_id": df[rid].astype(str).str.strip(),
                        "scope": df[scope].astype(str).str.strip().str.upper()})
    out["role"] = df[role].astype(str).str.strip().str.upper() if role else ""
    return out


def pilot_ids():
    return RID.findall(Path(PATHS["pilot_list"]).read_text())


def find_pdf(record_id):
    hits = sorted(Path(PATHS["pdf_dir"]).rglob(f"*{record_id}*.pdf"))
    return hits[0] if hits else None


def load_llm(model_key):
    """record_id -> parsed result for one model."""
    d = OUT / "llm" / slug(MODELS[model_key])
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("R*.json"))}


def to_vector(res):
    """Binary vector over the fields from one model result."""
    f = res.get("fields", {})
    return {fid: int(bool(f.get(fid, {}).get("present"))) for fid in field_ids()}


def kappa(x, y):
    x, y = list(x), list(y)
    n = len(x)
    if n == 0:
        return None, None
    po = sum(i == j for i, j in zip(x, y)) / n
    p1, p2 = sum(x) / n, sum(y) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    return (None if pe == 1 else (po - pe) / (1 - pe)), po

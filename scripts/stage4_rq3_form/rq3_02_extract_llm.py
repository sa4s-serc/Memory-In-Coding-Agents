"""Step 2. One LLM fills in the extraction form for every paper. Run once per model:

    export OLLAMA_API_KEY=...            (environment only, never in a file)
    python rq3_02_extract_llm.py --model A --only R00371 R00494     (pilot run: read the output first)
    python rq3_02_extract_llm.py --model A
    python rq3_02_extract_llm.py --model B

Resumes where it stopped. Output: results/llm/<model>/<record_id>.json, results/llm_raw/<model>/,
results/llm/<model>/_run.json (model, temperature, prompt SHA-256, start time).
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import time

import pandas as pd
import requests

from rq3_common import HERE, MODELS, OUT, THINK, field_ids, form, norm, slug

HOST = os.environ.get("OLLAMA_HOST", "https://ollama.com")
TEMPERATURE = 0.0


def build_prompt(rid, text):
    f = form()
    rules = "\n".join(f"{i}. {r}" for i, r in enumerate(f["rules"], 1))
    lines = []
    for fld in f["fields"]:
        lines.append(f"### {fld['id']} {fld['name']} ({fld['group']})\n{fld['definition']}\nIncludes:")
        for it in fld["includes"]:
            lines.append(f"- {it['item']}: {it['description']} Example: \"{it['example']}\"")
        lines.append("")
    tpl = (HERE / "prompt_extraction.md").read_text(encoding="utf-8")
    return tpl.format(rules=rules, fields="\n".join(lines), record_id=rid, text=text)


def call(model, prompt, think=None, retries=4):
    key = os.environ.get("OLLAMA_API_KEY")
    if not key:
        raise SystemExit("Set OLLAMA_API_KEY in the environment.")
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "format": "json",
            "stream": False, "options": {"temperature": TEMPERATURE}}
    if think is not None:
        body["think"] = think
    for a in range(retries):
        try:
            r = requests.post(f"{HOST}/api/chat", json=body, timeout=600,
                              headers={"Authorization": f"Bearer {key}"})
            r.raise_for_status()
            d = r.json()
            content = d["message"].get("content", "")
            if not content.strip():
                raise ValueError(f"empty answer (done_reason {d.get('done_reason')})")
            return content
        except Exception as e:
            if a == retries - 1:
                raise
            print(f"  retry {a + 1}: {e}")
            time.sleep(15 * (a + 1))


def parse(raw):
    """Strict JSON; if that fails, retry once with trailing commas before } or ] removed (a formatting
    slip seen with glm-5.3). The content is not changed; the repair is recorded in the output."""
    try:
        return json.loads(raw), False
    except json.JSONDecodeError:
        return json.loads(re.sub(r",(\s*[}\]])", r"\1", raw)), True


def check(res, text):
    src = norm(text)
    flags = []
    for fid in field_ids():
        fld = res.setdefault("fields", {}).setdefault(fid, {"present": False, "evidence": []})
        fld["present"] = bool(fld.get("present"))
        ev = fld.get("evidence") or []
        for e in ev:
            e["verbatim"] = bool(e.get("quote")) and norm(e["quote"]) in src
        if fld["present"] and not any(e.get("verbatim") for e in ev):
            flags.append(f"{fid}:no_verbatim_quote")
    res["flags"] = flags
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=sorted(MODELS), required=True)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    model, think = MODELS[a.model], THINK.get(a.model)
    papers = pd.read_csv(OUT / "papers.csv").record_id.tolist()
    if a.only:
        papers = [p for p in papers if p in a.only]
    out_dir, raw_dir = OUT / "llm" / slug(model), OUT / "llm_raw" / slug(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256((HERE / "prompt_extraction.md").read_bytes()
                         + (HERE / "extraction_form_v1.json").read_bytes()).hexdigest()
    (out_dir / "_run.json").write_text(json.dumps({"model": model, "host": HOST, "temperature": TEMPERATURE,
                                                   "think": "server default" if think is None else think,
                                                   "prompt_and_form_sha256": sha,
                                                   "started": dt.datetime.now().isoformat(timespec="seconds")},
                                                  indent=1))
    failed = []
    for i, rid in enumerate(papers, 1):
        if (out_dir / f"{rid}.json").exists():
            continue
        tp = OUT / "text" / f"{rid}.txt"
        if not tp.exists():
            print(f"[{i}/{len(papers)}] {rid}: no text, skipped")
            failed.append(rid)
            continue
        text = tp.read_text(encoding="utf-8")
        print(f"[{i}/{len(papers)}] {rid}")
        try:
            raw = call(model, build_prompt(rid, text), think)
            (raw_dir / f"{rid}.txt").write_text(raw, encoding="utf-8")
            parsed, repaired = parse(raw)
            res = check(parsed, text)
            res["record_id"] = rid
            if repaired:
                res["json_repaired"] = "trailing commas removed"
                print("  note: trailing commas removed from the JSON")
            (out_dir / f"{rid}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append(rid)
    done = [json.loads(p.read_text(encoding="utf-8")) for p in out_dir.glob("R*.json")]
    print(f"\nmodel {model}: papers done {len(done)}/{len(papers)}; failed {len(failed)} {failed}")
    print(f"fields filled {sum(f['present'] for r in done for f in r['fields'].values())}; "
          f"filled without a verbatim quote {sum(len(r['flags']) for r in done)}; "
          f"only boilerplate {sum(bool(r.get('only_boilerplate')) for r in done)}; "
          f"no limitation {sum(bool(r.get('no_limitation')) for r in done)}")


if __name__ == "__main__":
    main()

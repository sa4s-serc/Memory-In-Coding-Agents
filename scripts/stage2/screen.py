#!/usr/bin/env python3
"""
Stage 1 screening for the memory-in-coding-agents mapping study.

One script, one run per model. Writes JSONL checkpoints, resumes on restart.

  # discover what your subscription exposes
  python screen_stage1.py --provider ollama-cloud --list-models

  # pilot 50 records on Ollama Cloud (needs OLLAMA_API_KEY)
  python screen_stage1.py --provider ollama-cloud --model gpt-oss:20b \
                          --corpus merged_corpus_v2.csv --pilot 50 \
                          --batch-size 5 --max-tokens 16384 --reasoning-effort low

  # the earlier Gemini run, for a paired comparison on the same 50 records
  python screen_stage1.py --provider gemini --model gemini-2.5-flash-lite \
                          --corpus merged_corpus_v2.csv --pilot 50

  # local vLLM / llama.cpp / local Ollama
  python screen_stage1.py --provider openai-compat --base-url http://dgx:8000/v1 \
                          --model <local-model-id> --pilot 50

Outputs: results_<tag>.jsonl  (one line per record)
         failures_<tag>.jsonl (batches that never resolved)

The same --seed and --pilot draw the identical records the Gemini run saw, so the
two results_*.jsonl files are a record-for-record comparison of the probability
spread. That comparison, not a single model's elbow, is what the pilot decides.
"""

import argparse, csv, json, os, random, re, sys, time
from pathlib import Path

import requests

ABSTRACT_CHARS = 2200
MAX_BATCH_ATTEMPTS = 3        # content errors: bad JSON, missing refs
MAX_TRANSIENT_ATTEMPTS = 7    # transport errors: 429, 503


class Transient(Exception):
    """Rate limit or server error. Retry the batch, never split it."""
    def __init__(self, msg, retry_after=None):
        super().__init__(msg)
        self.retry_after = retry_after


class Fatal(Exception):
    """Auth or configuration error. Abort immediately, retrying cannot help."""

CRITERIA = """You are screening titles and abstracts for a systematic mapping study on
memory and information-handling mechanisms in LLM-based coding agents.

This is Stage 1 of a rapid review. Its job is RECALL: keep everything that might
be relevant so a later full-text stage can judge it. Wrongly excluding a relevant
paper here is unrecoverable; wrongly including an irrelevant one is cheap and gets
caught later. When a call is genuinely uncertain, lean toward inclusion.

INCLUSION
IC1: the record proposes, evaluates, studies, or benchmarks a memory or
     information-handling mechanism for an LLM-based agent. Information handling
     includes context compression, pruning, summarisation, context folding,
     scratchpads, retrieval over prior work, experience stores, skill libraries,
     self-evolving or self-improving behaviour, and cross-task knowledge capture
     or reuse. Whether the mechanism is the paper's central contribution or a
     prominent part of its system is a BUCKETING question (PRIMARY vs weaker),
     NOT an exclusion question. Do not exclude merely because memory looks
     secondary to some other contribution.
IC2: it is applied to, or evaluated on, code generation or software engineering
     tasks. Repository navigation, issue resolution, program repair, code
     completion, and long-horizon SWE agent work all count.

EXCLUSION
EC1: exclude only if the evaluation is purely conversational, QA, or a
     general-domain / non-code task with NO code or software engineering
     component at all.

Persistence across tasks is NOT an inclusion criterion. A mechanism scoped
entirely to a single task instance still satisfies IC1. Do not exclude on that
basis. Persistence is recorded later as a classification axis, not here.

Surveys and benchmarks are NOT excluded. A survey, review, position paper, or
benchmark that is on-topic for memory or information-handling in code/SE agents
SATISFIES screening even though it proposes no mechanism of its own. Bucket it
SURVEY or BENCHMARK and score it high when clearly on-topic. "No new mechanism",
"no novel contribution", "only a survey", or "only a benchmark" is NEVER by
itself grounds to exclude or to score below 0.5. Exclude a survey or benchmark
only when it fails IC2 or hits EC1.

BUCKET
PRIMARY   = proposes or evaluates a mechanism as a notable part of the work
SURVEY    = survey, review, or position paper
BENCHMARK = dataset or benchmark contribution
EXCLUDE   = fails IC2, or hits EC1

PROBABILITY
Report include as a probability from 0.0 to 1.0 that the record meets IC1 and IC2
and does not hit EC1. Use the FULL range, including mid values. Reserve 0.0-0.1
and 0.9-1.0 for records that are genuinely unambiguous from the abstract.

Some records are inherently borderline and MUST be scored in the middle band
(roughly 0.3-0.7), never at a pole:
  - a survey or benchmark whose code/SE focus is partial or unclear,
  - a paper where it is unclear whether memory is a real mechanism or just
    scaffolding or infrastructure,
  - a paper where the code/SE application is plausible but not stated outright,
  - any abstract too thin to decide.
Scoring these in the middle is correct behaviour, not indecision: it routes them
to human review, which is exactly where they belong. Do not force a verdict.

Keep each reason under 15 words."""

OUTPUT_SPEC = """Return a JSON object with a single key "records", holding one entry per
record in the same order, echoing the ref value verbatim. No prose, no markdown fences,
no trailing commentary.

{"records": [{"ref": "S01", "include": 0.0-1.0,
              "bucket": "PRIMARY|SURVEY|BENCHMARK|EXCLUDE", "reason": "one line"}]}"""

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string"},
                    "include": {"type": "number"},
                    "bucket": {"type": "string",
                               "enum": ["PRIMARY", "SURVEY", "BENCHMARK", "EXCLUDE"]},
                    "reason": {"type": "string"},
                },
                "required": ["ref", "include", "bucket", "reason"],
            },
        }
    },
    "required": ["records"],
}


# ---------------------------------------------------------------- corpus

def pick(fieldnames, candidates, what):
    lower = {f.lower().strip(): f for f in fieldnames}
    for c in candidates:
        if c in lower:
            return lower[c]
    sys.exit(f"could not find a {what} column in: {fieldnames}")


def load_corpus(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("empty corpus")
    fn = list(rows[0].keys())
    id_c = pick(fn, ["id", "record_id", "uid", "key"], "id")
    ti_c = pick(fn, ["title"], "title")
    ab_c = pick(fn, ["abstract", "description", "summary"], "abstract")
    src_c = next((f for f in fn if f.lower().strip() == "sources"), None)

    recs, seen = [], set()
    for r in rows:
        rid = (r[id_c] or "").strip()
        if not rid or rid in seen:
            continue
        seen.add(rid)
        recs.append({
            "id": rid,
            "title": (r[ti_c] or "").strip(),
            "abstract": (r[ab_c] or "").strip()[:ABSTRACT_CHARS],
            "sources": (r.get(src_c) or "").strip() if src_c else "",
        })
    return recs, {"id": id_c, "title": ti_c, "abstract": ab_c}


def coverage_report(recs, cols, log):
    """Abstract coverage is a precondition, not a detail. Surface it loudly."""
    n = len(recs)
    have = [r for r in recs if len(r["abstract"]) >= 100]
    thin = [r for r in recs if 0 < len(r["abstract"]) < 100]
    none_ = [r for r in recs if not r["abstract"]]
    lens = sorted(len(r["abstract"]) for r in have)

    log(f"columns used: id={cols['id']!r} title={cols['title']!r} "
        f"abstract={cols['abstract']!r}")
    log(f"abstracts: {len(have)}/{n} usable ({100*len(have)/n:.1f}%), "
        f"{len(thin)} under 100 chars, {len(none_)} empty")
    if lens:
        log(f"           median length {lens[len(lens)//2]} chars, "
            f"max {lens[-1]}")

    by_src = {}
    for r in recs:
        key = r["sources"] or "(unknown)"
        got, tot = by_src.get(key, (0, 0))
        by_src[key] = (got + (1 if len(r["abstract"]) >= 100 else 0), tot + 1)
    if len(by_src) > 1:
        log("           by source:")
        for k, (got, tot) in sorted(by_src.items(),
                                    key=lambda kv: -kv[1][1])[:8]:
            log(f"             {k:<28} {got}/{tot} ({100*got/tot:.0f}%)")

    if len(have) / n < 0.80:
        log("")
        log("  WARNING: under 80% of records carry a usable abstract.")
        log("  Screening on titles alone will not hold up. Backfill from")
        log("  Crossref or OpenAlex before the full run, or pass")
        log("  --skip-no-abstract to defer them to a separate pass.")
        log("")
    return len(have) / n


def load_done(path):
    done = set()
    if Path(path).exists():
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    done.add(json.loads(line)["id"])
                except Exception:
                    pass
    return done


# ---------------------------------------------------------------- prompt

def build_prompt(batch):
    lines = []
    for i, rec in enumerate(batch, 1):
        ref = f"S{i:02d}"
        rec["_ref"] = ref
        ab = rec["abstract"] or "[no abstract available]"
        lines.append(f'ref: {ref}\ntitle: {rec["title"]}\nabstract: {ab}')
    body = "\n\n---\n\n".join(lines)
    return (f"{CRITERIA}\n\n{OUTPUT_SPEC}\n\nScreen the following "
            f"{len(batch)} records.\n\n{body}")


def parse_json_array(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, flags=re.S)
        if not m:
            raise
        obj = json.loads(m.group(0))
    if isinstance(obj, dict):
        for k in ("records", "results", "items"):
            if k in obj:
                obj = obj[k]
                break
    if not isinstance(obj, list):
        raise ValueError("response is not a JSON array")
    return obj


def validate(batch, parsed):
    """Match on echoed ref. Never fall back to positional order."""
    if len(parsed) != len(batch):
        raise ValueError(f"expected {len(batch)} objects, got {len(parsed)}")
    by_ref = {}
    for o in parsed:
        ref = str(o.get("ref", "")).strip()
        if ref in by_ref:
            raise ValueError(f"duplicate ref {ref}")
        by_ref[ref] = o
    out = []
    for rec in batch:
        o = by_ref.get(rec["_ref"])
        if o is None:
            raise ValueError(f"missing ref {rec['_ref']} ({rec['id'][:40]})")
        try:
            p = float(o["include"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"bad include value for {rec['_ref']}")
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"include out of range for {rec['_ref']}: {p}")
        bucket = str(o.get("bucket", "")).strip().upper()
        if bucket not in {"PRIMARY", "SURVEY", "BENCHMARK", "EXCLUDE"}:
            raise ValueError(f"bad bucket for {rec['_ref']}: {bucket!r}")
        out.append({
            "id": rec["id"],
            "title": rec["title"],
            "include": p,
            "bucket": bucket,
            "reason": str(o.get("reason", ""))[:400],
            "abstract_chars": len(rec["abstract"]),
        })
    return out


# ---------------------------------------------------------------- clients

class Gemini:
    """Free tier. Watch RPM and RPD; --sleep is your rate limiter."""
    def __init__(self, model, key, max_tokens=8192, thinking_budget=0):
        self.model, self.key = model, key
        self.max_tokens = max_tokens
        self.thinking_budget = thinking_budget
        self.url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent")

    def __call__(self, prompt):
        gen = {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "maxOutputTokens": self.max_tokens,
        }
        if self.thinking_budget is not None:
            gen["thinkingConfig"] = {"thinkingBudget": self.thinking_budget}
        payload = {"contents": [{"parts": [{"text": prompt}]}],
                   "generationConfig": gen}

        r = requests.post(self.url, params={"key": self.key},
                          json=payload, timeout=240)

        if r.status_code in (429, 500, 502, 503):
            detail, delay = "", None
            try:
                err = r.json().get("error", {})
                detail = err.get("message", "")[:200]
                for d in err.get("details", []):
                    if "retryDelay" in d:
                        delay = float(str(d["retryDelay"]).rstrip("s"))
            except Exception:
                pass
            raise Transient(f"http {r.status_code}: {detail}", delay)

        if r.status_code in (400, 401, 403, 404):
            try:
                msg = r.json().get("error", {}).get("message", "")[:300]
            except Exception:
                msg = r.text[:300]
            raise Fatal(
                f"http {r.status_code} on model {self.model!r}: {msg}\n"
                f"  list callable models with:\n"
                f"  curl -s 'https://generativelanguage.googleapis.com/"
                f"v1beta/models?key=$GEMINI_API_KEY'")
        r.raise_for_status()

        d = r.json()
        cand = d["candidates"][0]
        text = "".join(p.get("text", "")
                       for p in cand.get("content", {}).get("parts", []))
        if cand.get("finishReason") == "MAX_TOKENS":
            raise ValueError("hit maxOutputTokens, raise --max-tokens "
                             "or lower --batch-size")
        return text


class OpenAICompat:
    """vLLM, llama.cpp --server, local Ollama, and Ollama Cloud all speak this.

    Local vLLM/llama.cpp/Ollama ignore the key, so 'none' is fine there.
    Ollama Cloud (https://ollama.com/v1) REQUIRES a real bearer key; pass it in.
    """
    def __init__(self, model, base_url, key="none", json_mode=True,
                 schema=True, max_tokens=4096, reasoning_effort=None):
        self.model = model
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.key = key
        self.json_mode = json_mode
        self.schema = schema
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort

    def __call__(self, prompt):
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": self.max_tokens,
            "seed": 0,
        }
        if self.reasoning_effort:
            # Accepted by gpt-oss and several reasoning models on the OpenAI shim.
            # Keeping it low protects the JSON budget and speeds screening.
            payload["reasoning_effort"] = self.reasoning_effort
        if self.json_mode and self.schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "screening", "schema": RESPONSE_SCHEMA},
            }
        elif self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        r = requests.post(self.url, json=payload, timeout=600,
                          headers={"Authorization": f"Bearer {self.key}"})
        if r.status_code in (429, 500, 502, 503):
            raise Transient(f"http {r.status_code}: {r.text[:200]}")
        if r.status_code in (400, 401, 403, 404):
            raise Fatal(f"http {r.status_code} on model {self.model!r}: "
                        f"{r.text[:300]}")
        r.raise_for_status()
        choice = r.json()["choices"][0]
        if choice.get("finish_reason") == "length":
            raise ValueError("hit max_tokens (output truncated). Raise "
                             "--max-tokens, lower --batch-size, or lower "
                             "--reasoning-effort")
        msg = choice["message"]
        content = msg.get("content") or ""
        # Some reasoning models return an empty content with the answer tucked
        # under a non-standard key; fall back rather than crash the batch.
        if not content.strip():
            content = msg.get("reasoning_content") or msg.get("text") or ""
        return content


# ---------------------------------------------------------------- model listing

def list_openai_models(base_url, key, log):
    url = base_url.rstrip("/") + "/models"
    r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=60)
    if r.status_code in (401, 403):
        sys.exit(f"auth failed listing models ({r.status_code}). Check the key.")
    r.raise_for_status()
    data = r.json().get("data", [])
    ids = sorted(m.get("id", "") for m in data if m.get("id"))
    log(f"{len(ids)} models available at {url}:")
    for i in ids:
        log(f"  {i}")
    return ids


# ---------------------------------------------------------------- distribution

def summarise_results(path, log):
    """Print the include-probability histogram and bucket counts.

    This is the whole point of the pilot: see the middle, not just the edges.
    """
    if not Path(path).exists():
        return
    probs, buckets = [], {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except Exception:
                continue
            probs.append(float(row["include"]))
            b = row.get("bucket", "?")
            buckets[b] = buckets.get(b, 0) + 1
    if not probs:
        return
    n = len(probs)
    edges = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]
    counts = [0] * (len(edges) - 1)
    for p in probs:
        for j in range(len(edges) - 1):
            if edges[j] <= p < edges[j + 1]:
                counts[j] += 1
                break
    log("")
    log(f"include-probability distribution (n={n}):")
    peak = max(counts) or 1
    for j in range(len(edges) - 1):
        lo, hi = edges[j], min(edges[j + 1], 1.0)
        bar = "#" * int(40 * counts[j] / peak)
        log(f"  {lo:.1f}-{hi:.1f}  {counts[j]:4d}  {bar}")
    mid = sum(1 for p in probs if 0.2 <= p <= 0.8)
    log(f"middle band 0.2-0.8: {mid}/{n} ({100*mid/n:.0f}%)   "
        f"a wide middle here is the construct, not the model")
    log("buckets: " + ", ".join(f"{k}={v}" for k, v in sorted(buckets.items())))


# ---------------------------------------------------------------- driver

def run_batch(client, batch, log):
    """Content errors retry then split. Transport errors back off, never split."""
    content_tries = transient_tries = 0
    last = None

    while True:
        try:
            txt = client(build_prompt(batch))
            return validate(batch, parse_json_array(txt)), True

        except Fatal:
            raise

        except Transient as e:
            last = e
            transient_tries += 1
            if transient_tries >= MAX_TRANSIENT_ATTEMPTS:
                log(f"    quota exhausted after {transient_tries} waits: {e}")
                return [], False
            wait = e.retry_after if e.retry_after else min(60, 2 ** transient_tries)
            log(f"    transient ({transient_tries}/{MAX_TRANSIENT_ATTEMPTS}), "
                f"waiting {wait:.0f}s: {e}")
            time.sleep(wait)

        except Exception as e:
            last = e
            content_tries += 1
            log(f"    content error {content_tries}/{MAX_BATCH_ATTEMPTS}: {e}")
            if content_tries >= MAX_BATCH_ATTEMPTS:
                break
            time.sleep(2 * content_tries)

    if len(batch) == 1:
        log(f"    giving up on {batch[0]['id'][:60]}: {last}")
        return [], False

    log(f"    splitting batch of {len(batch)} into singletons")
    rows, ok = [], True
    for rec in batch:
        r, o = run_batch(client, [rec], log)
        rows.extend(r)
        ok = ok and o
    return rows, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="merged_corpus.csv")
    ap.add_argument("--provider",
                    choices=["gemini", "openai-compat", "ollama-cloud"],
                    required=True)
    ap.add_argument("--model", help="required unless --list-models")
    ap.add_argument("--base-url",
                    help="openai-compat only, e.g. http://dgx:8000/v1. "
                         "ollama-cloud defaults to https://ollama.com/v1")
    ap.add_argument("--api-key-env", default="GEMINI_API_KEY",
                    help="env var holding the key. Defaults: GEMINI_API_KEY for "
                         "gemini, OLLAMA_API_KEY for ollama-cloud")
    ap.add_argument("--list-models", action="store_true",
                    help="list models the provider exposes, then exit")
    ap.add_argument("--reasoning-effort", choices=["low", "medium", "high"],
                    help="reasoning models only (e.g. gpt-oss). Use 'low' for "
                         "screening to protect the JSON budget")
    ap.add_argument("--no-json-mode", action="store_true",
                    help="drop response_format if the local server rejects it")
    ap.add_argument("--no-schema", action="store_true",
                    help="use plain json_object instead of json_schema")
    ap.add_argument("--max-tokens", type=int, default=8192,
                    help="output budget; must fit inside vLLM --max-model-len")
    ap.add_argument("--thinking-budget", type=int, default=0,
                    help="gemini only; 0 disables reasoning tokens, -1 for dynamic")
    ap.add_argument("--tag", help="output file tag, defaults to model name")
    ap.add_argument("--batch-size", type=int, default=10)
    ap.add_argument("--sleep", type=float, default=0.0, help="seconds between calls")
    ap.add_argument("--pilot", type=int, default=0,
                    help="screen only N records, sampled with --seed")
    ap.add_argument("--seed", type=int, default=20260802)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the first batch prompt verbatim and exit, no API call")
    ap.add_argument("--ids-file",
                    help="screen only ids listed in this file, one per line "
                         "(overrides --pilot); use for the QGS pre-flight")
    ap.add_argument("--slice",
                    help="screen a contiguous slice of the corpus after a stable "
                         "sort by id, e.g. 0:250. For batched full-corpus runs.")
    ap.add_argument("--skip-no-abstract", action="store_true",
                    help="defer records with under 100 chars of abstract")
    args = ap.parse_args()

    def log(m):
        print(m, flush=True)

    # Provider defaults: base URL and key env are inferred for ollama-cloud.
    if args.provider == "ollama-cloud":
        if not args.base_url:
            args.base_url = "https://ollama.com/v1"
        if args.api_key_env == "GEMINI_API_KEY":
            args.api_key_env = "OLLAMA_API_KEY"
        # Ollama Cloud shim is unreliable on json_schema; default to json_object.
        args.no_schema = True

    # --list-models needs a key + base url but no model and no corpus.
    if args.list_models:
        if args.provider == "gemini":
            key = os.environ.get(args.api_key_env or "GEMINI_API_KEY")
            if not key:
                sys.exit(f"{args.api_key_env} not set")
            r = requests.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": key}, timeout=60)
            r.raise_for_status()
            for m in r.json().get("models", []):
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    log(m.get("name", ""))
            return
        base = args.base_url or "https://ollama.com/v1"
        key = os.environ.get(args.api_key_env, "none")
        list_openai_models(base, key, log)
        return

    if not args.model:
        sys.exit("--model is required (or pass --list-models to discover one)")

    tag = args.tag or re.sub(r"[^A-Za-z0-9._-]", "_", args.model)
    if args.ids_file:
        tag = f"{tag}_ids"
    elif args.pilot:
        tag = f"{tag}_pilot{args.pilot}"
    out_path = f"results_{tag}.jsonl"
    fail_path = f"failures_{tag}.jsonl"

    records, cols = load_corpus(args.corpus)
    log(f"corpus: {len(records)} unique records")
    coverage_report(records, cols, log)

    if args.skip_no_abstract:
        before = len(records)
        deferred = [r for r in records if len(r["abstract"]) < 100]
        records = [r for r in records if len(r["abstract"]) >= 100]
        with open(f"deferred_{tag}.jsonl", "w", encoding="utf-8") as fh:
            for r in deferred:
                fh.write(json.dumps({"id": r["id"], "title": r["title"],
                                     "abstract_chars": len(r["abstract"])}) + "\n")
        log(f"deferred {before - len(records)} records lacking abstracts "
            f"-> deferred_{tag}.jsonl")

    if args.ids_file:
        wanted = [ln.strip() for ln in open(args.ids_file, encoding="utf-8")
                  if ln.strip() and not ln.startswith("#")]
        have = {r["id"] for r in records}
        missing = [w for w in wanted if w not in have]
        records = [r for r in records if r["id"] in set(wanted)]
        log(f"ids-file: {len(records)}/{len(wanted)} matched")
        if missing:
            log(f"  NOT IN CORPUS ({len(missing)}): {', '.join(missing[:12])}")
        if not records:
            sys.exit("no ids matched; check the id format in the file")
    elif args.pilot:
        rng = random.Random(args.seed)
        records = rng.sample(records, min(args.pilot, len(records)))
        log(f"pilot: {len(records)} records, seed {args.seed}")

    if args.slice:
        try:
            lo, hi = (int(x) for x in args.slice.split(":"))
        except Exception:
            sys.exit("--slice must look like START:END, e.g. 0:250")
        # Stable, reproducible order so batch boundaries never shift between runs.
        records = sorted(records, key=lambda r: r["id"])[lo:hi]
        log(f"slice [{lo}:{hi}] over id-sorted corpus: {len(records)} records")
        if not records:
            sys.exit(f"slice {args.slice} is empty; corpus has fewer records")

    if args.dry_run:
        first = records[:args.batch_size]
        log("\n" + "=" * 70)
        log(build_prompt(first))
        log("=" * 70)
        log(f"\n{len(first)} records, "
            f"{sum(len(r['abstract']) for r in first)} abstract chars total")
        return

    if args.provider == "gemini":
        key = os.environ.get(args.api_key_env)
        if not key:
            sys.exit(f"{args.api_key_env} not set")
        client = Gemini(args.model, key, max_tokens=args.max_tokens,
                        thinking_budget=args.thinking_budget)
    else:
        if not args.base_url:
            sys.exit("--base-url required for openai-compat")
        # Local servers ignore the key; Ollama Cloud requires it.
        key = os.environ.get(args.api_key_env, "none")
        if args.provider == "ollama-cloud" and key == "none":
            sys.exit(f"{args.api_key_env} not set (Ollama Cloud needs a real key "
                     f"from ollama.com/settings/keys)")
        client = OpenAICompat(args.model, args.base_url, key=key,
                              json_mode=not args.no_json_mode,
                              schema=not args.no_schema,
                              max_tokens=args.max_tokens,
                              reasoning_effort=args.reasoning_effort)
        log(f"provider={args.provider} model={args.model!r} "
            f"base_url={args.base_url} schema={not args.no_schema} "
            f"reasoning_effort={args.reasoning_effort}")

    done = load_done(out_path)
    todo = [r for r in records if r["id"] not in done]
    log(f"already done: {len(done)}, to screen: {len(todo)}")

    batches = [todo[i:i + args.batch_size]
               for i in range(0, len(todo), args.batch_size)]
    t0 = time.time()

    with open(out_path, "a", encoding="utf-8") as out, \
         open(fail_path, "a", encoding="utf-8") as fail:
        for n, batch in enumerate(batches, 1):
            try:
                rows, ok = run_batch(client, batch, log)
            except Fatal as e:
                log(f"\nFATAL: {e}")
                log("nothing further attempted; fix the config and rerun.")
                sys.exit(2)
            for row in rows:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            if not ok:
                got = {r["id"] for r in rows}
                for rec in batch:
                    if rec["id"] not in got:
                        fail.write(json.dumps({"id": rec["id"],
                                               "title": rec["title"]}) + "\n")
                fail.flush()
            rate = (time.time() - t0) / n
            log(f"[{n}/{len(batches)}] +{len(rows)} rows  "
                f"{rate:.1f}s/batch  eta {rate * (len(batches) - n) / 60:.0f} min")
            if args.sleep:
                time.sleep(args.sleep)

    log(f"done -> {out_path}")
    summarise_results(out_path, log)


if __name__ == "__main__":
    main()
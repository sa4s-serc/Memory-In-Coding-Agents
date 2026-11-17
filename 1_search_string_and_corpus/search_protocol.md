# Search protocol

## Search string
Four concept blocks over title, abstract and keywords. Terms are ORed within a block; blocks are ANDed.

| Block | Concept | Terms |
|---|---|---|
| L | Model / agent class | "large language model*", LLM*, "language model*", "foundation model*", "coding agent*", "code agent*", "software engineering agent*", "SWE agent*" |
| G | Agent | agent*, agentic, "multi-agent" |
| M | Memory / information handling | memory, experience, reflection, trajector*, "continual learning", "lifelong learning", self-improv*, self-evolv*, "knowledge accumulation", "skill librar*", "case-based reasoning", "context management", "context compression", "context pruning", "context folding" |
| C | Code / SE | "software engineering", "software development", "code generation", "code completion", "program repair", "issue resolution", "bug fix*", repositor*, codebase, "SWE-bench", "SWE-agent", "coding agent*", "software agent*", SWE |

Full Scopus query: `search_string.txt`. The string was revised once against the quasi-gold standard (terms added to L, M and C) and then fixed on 2 August 2026.

## Sources
| Source | How the string was applied | Script |
|---|---|---|
| Scopus (Documents) | String run directly in the Scopus interface; results exported | manual export |
| arXiv | API queried with each C term AND the M block (title, abstract; wildcards expanded); blocks L, M, C then applied locally by regex over title and abstract | `arxiv_harvest.py` |
| OpenAlex | API queried with each C term AND the M block AND the L block (title and abstract, from 2023-01-01); blocks L, M, C then applied locally by regex; non-study record types removed | `openalex_harvest.py`, `filter_types.py` |

arXiv and OpenAlex cover the preprint literature, for which the Scopus Preprints collection offers no bulk export. Block G was not applied in the local membership test; the agent requirement was enforced at screening through IC1.

## Merge
Records were merged in the order Scopus, arXiv, OpenAlex and deduplicated by DOI, then arXiv ID, then normalised title, then fuzzy title match (ratio >= 92) (`dedup_corpus.py`). Result: 2,411 unique records (`corpus.csv`).

## Validation
Quasi-gold standard (QGS) of 25 papers (`quasi_gold_standard_test/qgs.csv`), assembled from prior reading and snowballing, labelled against `definitions.md`. Recall of the merged corpus: 24/25 (96.0%, Wilson 95% CI [80.5%, 99.3%]). Part of the quasi-gold standard was used when revising the string.
